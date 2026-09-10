package infra

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"github.com/google/uuid"
	amqp "github.com/rabbitmq/amqp091-go"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/types/known/timestamppb"

	eventsv1 "mirea-crm/gen/go/mirea/events/v1"
)

const Exchange = "mirea.events"

// EventPublisher шлёт доменные события в RabbitMQ. Тело — protobuf-JSON,
// а не бинарь: типы общие с Python-сервисами, но сообщения читаются глазами
// в management-панели.
type EventPublisher struct {
	conn     *amqp.Connection
	channel  *amqp.Channel
	producer string
}

func NewEventPublisher(url, producer string) (*EventPublisher, error) {
	conn, err := amqp.Dial(url)
	if err != nil {
		return nil, fmt.Errorf("подключение к RabbitMQ: %w", err)
	}

	channel, err := conn.Channel()
	if err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("канал RabbitMQ: %w", err)
	}
	if err := channel.Confirm(false); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("режим подтверждений: %w", err)
	}
	if err := channel.ExchangeDeclare(Exchange, "topic", true, false, false, false, nil); err != nil {
		_ = conn.Close()
		return nil, fmt.Errorf("объявление обменника: %w", err)
	}

	slog.Info("подключён к RabbitMQ", "exchange", Exchange)
	return &EventPublisher{conn: conn, channel: channel, producer: producer}, nil
}

func (p *EventPublisher) Close() {
	if p.channel != nil {
		_ = p.channel.Close()
	}
	if p.conn != nil {
		_ = p.conn.Close()
	}
}

func (p *EventPublisher) Publish(
	ctx context.Context, routingKey string, envelope *eventsv1.EventEnvelope,
) error {
	envelope.EventId = uuid.NewString()
	envelope.RoutingKey = routingKey
	envelope.OccurredAt = timestamppb.New(time.Now().UTC())
	envelope.Producer = p.producer
	ctx, span := PublishSpan(ctx, routingKey)
	defer span.End()

	envelope.Traceparent = TraceparentFrom(ctx)
	envelope.Actor = CallerFrom(ctx).Subject

	body, err := protojson.Marshal(envelope)
	if err != nil {
		return fmt.Errorf("сериализация события: %w", err)
	}

	err = p.channel.PublishWithContext(ctx, Exchange, routingKey, false, false, amqp.Publishing{
		ContentType:  "application/json",
		MessageId:    envelope.EventId,
		Type:         routingKey,
		DeliveryMode: amqp.Persistent,
		Body:         body,
	})
	if err != nil {
		FailSpan(span, err)
		return fmt.Errorf("публикация %s: %w", routingKey, err)
	}
	CountEventPublished(p.producer, routingKey)

	slog.DebugContext(ctx, "опубликовано", "routing_key", routingKey, "event_id", envelope.EventId)
	return nil
}

// Ping — активная проверка для readiness: соединение amqp091 не сообщает
// о разрыве, пока не попробуешь им воспользоваться.
func (p *EventPublisher) Ping(ctx context.Context) error {
	if p.conn == nil || p.conn.IsClosed() {
		return fmt.Errorf("соединение закрыто")
	}
	channel, err := p.conn.Channel()
	if err != nil {
		return err
	}
	defer channel.Close()
	return channel.ExchangeDeclarePassive(Exchange, "topic", true, false, false, false, nil)
}
