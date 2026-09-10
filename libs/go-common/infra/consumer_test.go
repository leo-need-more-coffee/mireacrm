package infra

import (
	"context"
	"testing"

	amqp "github.com/rabbitmq/amqp091-go"
	"google.golang.org/protobuf/encoding/protojson"

	eventsv1 "mirea-crm/gen/go/mirea/events/v1"
)

// acknowledger подменяет подтверждения брокера: проверяется решение
// потребителя, а не доставка.
type acknowledger struct {
	acked       bool
	nacked      bool
	nackRequeue bool
}

func (a *acknowledger) Ack(uint64, bool) error { a.acked = true; return nil }

func (a *acknowledger) Nack(_ uint64, _ bool, requeue bool) error {
	a.nacked = true
	a.nackRequeue = requeue
	return nil
}

func (a *acknowledger) Reject(_ uint64, requeue bool) error {
	a.nacked = true
	a.nackRequeue = requeue
	return nil
}

func delivery(t *testing.T, routingKey string, delivered int) (amqp.Delivery, *acknowledger) {
	t.Helper()

	body, err := protojson.Marshal(&eventsv1.EventEnvelope{
		EventId:    "7f4c1e2a-0000-4000-8000-000000000001",
		RoutingKey: routingKey,
		Producer:   "tests",
	})
	if err != nil {
		t.Fatalf("конверт не собрался: %v", err)
	}

	ack := &acknowledger{}
	headers := amqp.Table{}
	if delivered > 0 {
		headers["x-delivery-count"] = int64(delivered)
	}
	return amqp.Delivery{
		Acknowledger: ack,
		Body:         body,
		Type:         routingKey,
		Headers:      headers,
	}, ack
}

func consumerWith(handler Handler) *Consumer {
	return &Consumer{
		service: "tests",
		queue:   "tests.events",
		routes:  map[string]Handler{"appointment.completed": handler},
	}
}

// Пауза перед возвратом здесь не нужна: проверяется решение, а не сон.
func withoutWaiting(t *testing.T) {
	t.Helper()
	previous, previousMax := retryDelay, retryDelayMax
	retryDelay, retryDelayMax = 0, 0
	t.Cleanup(func() { retryDelay, retryDelayMax = previous, previousMax })
}

// Сосед перезапускается — событие возвращается в очередь, а не хоронится.
// До появления повторов перезапуск booking навсегда терял списание материалов.
func TestUnavailableNeighbourIsRetried(t *testing.T) {
	withoutWaiting(t)

	message, ack := delivery(t, "appointment.completed", 0)
	consumerWith(func(context.Context, *eventsv1.EventEnvelope) error {
		return Unavailable("catalog", nil)
	}).dispatch(context.Background(), message)

	if !ack.nacked || !ack.nackRequeue {
		t.Errorf("ожидался возврат в очередь, получено nacked=%v requeue=%v",
			ack.nacked, ack.nackRequeue)
	}
}

// Повтор не бесконечен: исчерпав попытки, событие уходит в dead-letter.
func TestRetriesAreBounded(t *testing.T) {
	withoutWaiting(t)

	message, ack := delivery(t, "appointment.completed", RetryLimit-1)
	consumerWith(func(context.Context, *eventsv1.EventEnvelope) error {
		return Unavailable("catalog", nil)
	}).dispatch(context.Background(), message)

	if !ack.nacked || ack.nackRequeue {
		t.Errorf("ожидался dead-letter, получено nacked=%v requeue=%v",
			ack.nacked, ack.nackRequeue)
	}
}

// Повторять нечего: следующая попытка разобьётся о то же самое.
func TestInvalidPayloadIsNotRetried(t *testing.T) {
	withoutWaiting(t)

	message, ack := delivery(t, "appointment.completed", 0)
	consumerWith(func(context.Context, *eventsv1.EventEnvelope) error {
		return InvalidArgument("service_id не разобран")
	}).dispatch(context.Background(), message)

	if !ack.nacked || ack.nackRequeue {
		t.Errorf("ожидался dead-letter, получено nacked=%v requeue=%v",
			ack.nacked, ack.nackRequeue)
	}
}

func TestSuccessIsAcknowledged(t *testing.T) {
	message, ack := delivery(t, "appointment.completed", 0)
	consumerWith(func(context.Context, *eventsv1.EventEnvelope) error {
		return nil
	}).dispatch(context.Background(), message)

	if !ack.acked {
		t.Error("успешная обработка должна подтверждаться")
	}
}

// Иначе очередь встанет на событии, которое никому не нужно.
func TestUnsubscribedKeyIsAcknowledged(t *testing.T) {
	message, ack := delivery(t, "stock.low", 0)
	consumerWith(func(context.Context, *eventsv1.EventEnvelope) error {
		t.Error("обработчик не должен вызываться")
		return nil
	}).dispatch(context.Background(), message)

	if !ack.acked {
		t.Error("событие без обработчика должно подтверждаться")
	}
}

// Счётчик попыток ведёт брокер: quorum-очередь проставляет x-delivery-count
// при каждом возврате. Без него лимит повторов не с чем сравнивать.
func TestAttemptCountsBrokerRedeliveries(t *testing.T) {
	if attempt(amqp.Delivery{Headers: amqp.Table{}}) != 1 {
		t.Error("первая доставка — это первая попытка")
	}
	if got := attempt(amqp.Delivery{Headers: amqp.Table{"x-delivery-count": int64(3)}}); got != 4 {
		t.Errorf("счётчик брокера не учтён: %d", got)
	}
}
