package infra

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
	"google.golang.org/protobuf/encoding/protojson"

	eventsv1 "mirea-crm/gen/go/mirea/events/v1"
)

// Handler обрабатывает одно событие. Возвращённая ошибка означает повтор:
// событие вернётся в очередь и будет обработано снова, пока не исчерпает
// RetryLimit. InvalidArgumentError повтора не получает — разбираться в
// заведомо неверном payload брокеру нечем.
type Handler func(ctx context.Context, envelope *eventsv1.EventEnvelope) error

type Consumer struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	queue   string
	service string
	routes  map[string]Handler
}

func NewConsumer(url, queue, service string) (*Consumer, error) {
	conn, err := amqp.Dial(url)
	if err != nil {
		return nil, fmt.Errorf("подключение к RabbitMQ: %w", err)
	}

	channel, err := conn.Channel()
	if err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("канал RabbitMQ: %w", err)
	}
	// Без ограничения брокер вывалит в потребителя всю очередь разом,
	// и при падении процесса вся пачка вернётся необработанной.
	if err := channel.Qos(16, 0, false); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("prefetch: %w", err)
	}

	return &Consumer{
		conn: conn, channel: channel, queue: queue, service: service,
		routes: map[string]Handler{},
	}, nil
}

func (c *Consumer) Handle(routingKey string, handler Handler) {
	c.routes[routingKey] = handler
}

func (c *Consumer) Close() {
	if c.channel != nil {
		_ = c.channel.Close()
	}
	if c.conn != nil {
		_ = c.conn.Close()
	}
}

// Run читает очередь до отмены контекста. Очередь и биндинги объявлены
// декларативно в deploy/rabbitmq/definitions.json, потребитель их не создаёт.
func (c *Consumer) Run(ctx context.Context) error {
	// Именно Consume, а не ConsumeWithContext: последний на отмене контекста
	// шлёт basic.cancel из собственной горутины, и тот сталкивается с
	// channel.close из Close. Два RPC ждут ответа на одном канале, ответ
	// достаётся не тому — закрытие зависает навсегда. Подписку снимает
	// закрытие канала, отдельная отмена не нужна.
	deliveries, err := c.channel.Consume(c.queue, "", false, false, false, false, nil)
	if err != nil {
		return fmt.Errorf("подписка на %s: %w", c.queue, err)
	}
	slog.Info("слушаем очередь", "queue", c.queue)

	for {
		select {
		case <-ctx.Done():
			return nil
		case delivery, ok := <-deliveries:
			if !ok {
				return fmt.Errorf("канал доставки закрыт")
			}
			c.dispatch(ctx, delivery)
		}
	}
}

// Ошибка обработчика чаще всего транзиентная: сосед перезапускается, база
// моргнула. Повторить безопасно — обработчики идемпотентны, отметка об
// обработке пишется той же транзакцией, что и эффект. Поэтому событие
// возвращается в очередь, а не уходит в dead-letter с первой же осечки:
// иначе перезапуск соседа навсегда терял бы списание материалов.
const RetryLimit = 5

// Пауза растёт с попытками: без неё лимит сгорает за миллисекунды, пока
// сосед ещё поднимается, и повтор не успевает ничего исправить.
var (
	retryDelay    = 500 * time.Millisecond
	retryDelayMax = 5 * time.Second
)

// attempt — какая это попытка по счёту. Счётчик ведёт брокер: quorum-очередь
// проставляет x-delivery-count при каждом возврате.
func attempt(delivery amqp.Delivery) int {
	switch value := delivery.Headers["x-delivery-count"].(type) {
	case int64:
		return int(value) + 1
	case int32:
		return int(value) + 1
	case int:
		return value + 1
	default:
		return 1
	}
}

func (c *Consumer) retryOrBury(
	ctx context.Context, delivery amqp.Delivery,
	envelope *eventsv1.EventEnvelope, err error, log *slog.Logger,
) {
	// Повторять нечего: payload не проходит проверку, и следующая попытка
	// разобьётся о то же самое.
	var invalid *InvalidArgumentError
	tries := attempt(delivery)

	if errors.As(err, &invalid) || tries >= RetryLimit {
		log.Error("обработка не удалась окончательно", "error", err, "attempt", tries)
		CountEventConsumed(c.service, envelope.GetRoutingKey(), "failed")
		_ = delivery.Nack(false, false)
		return
	}

	log.Warn("обработка не удалась, вернём в очередь", "error", err, "attempt", tries)
	CountEventConsumed(c.service, envelope.GetRoutingKey(), "retried")

	pause := time.Duration(tries) * retryDelay
	if pause > retryDelayMax {
		pause = retryDelayMax
	}
	select {
	case <-ctx.Done():
	case <-time.After(pause):
	}
	_ = delivery.Nack(false, true)
}

func (c *Consumer) dispatch(ctx context.Context, delivery amqp.Delivery) {
	var envelope eventsv1.EventEnvelope
	if err := protojson.Unmarshal(delivery.Body, &envelope); err != nil {
		slog.Error("не разобрали событие", "error", err, "message_id", delivery.MessageId)
		// Ключ берём из свойства сообщения: конверт не разобран, а без метки
		// такие отказы не видны в статистике вовсе.
		key := delivery.Type
		if key == "" {
			key = "unknown"
		}
		CountEventConsumed(c.service, key, "unparsable")
		_ = delivery.Nack(false, false)
		return
	}

	// Трасса продолжается: контекст пришёл вместе с событием.
	ctx, span := ConsumeSpan(ctx, envelope.GetRoutingKey(), envelope.GetTraceparent())
	defer span.End()

	ctx = WithTraceparent(ctx, ParseTraceparent(envelope.GetTraceparent()))
	log := slog.With(
		"routing_key", envelope.GetRoutingKey(),
		"event_id", envelope.GetEventId(),
		"trace_id", TraceID(Traceparent(ctx)),
	)

	handler, ok := c.routes[envelope.GetRoutingKey()]
	if !ok {
		// На ключ никто не подписан — подтверждаем, иначе очередь встанет.
		log.Warn("обработчик не найден")
		CountEventConsumed(c.service, envelope.GetRoutingKey(), "skipped")
		_ = delivery.Ack(false)
		return
	}

	if err := handler(ctx, &envelope); err != nil {
		FailSpan(span, err)
		c.retryOrBury(ctx, delivery, &envelope, err, log)
		return
	}

	log.Debug("обработано")
	CountEventConsumed(c.service, envelope.GetRoutingKey(), "handled")
	_ = delivery.Ack(false)
}

// Ping — активная проверка для readiness: соединение amqp091 не сообщает
// о разрыве, пока не попробуешь им воспользоваться.
func (c *Consumer) Ping(ctx context.Context) error {
	if c.conn == nil || c.conn.IsClosed() {
		return fmt.Errorf("соединение закрыто")
	}
	channel, err := c.conn.Channel()
	if err != nil {
		return err
	}
	defer channel.Close()
	_, err = channel.QueueDeclarePassive(c.queue, true, false, false, false, nil)
	return err
}
