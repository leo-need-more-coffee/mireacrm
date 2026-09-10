package infra

import (
	"context"
	"fmt"
	"log/slog"

	amqp "github.com/rabbitmq/amqp091-go"
	"google.golang.org/protobuf/encoding/protojson"

	eventsv1 "mirea-crm/gen/go/mirea/events/v1"
)

// Handler обрабатывает одно событие. Возвращённая ошибка означает, что
// сообщение уйдёт в dead-letter: повторять его бессмысленно или опасно.
type Handler func(ctx context.Context, envelope *eventsv1.EventEnvelope) error

type Consumer struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	queue   string
	routes  map[string]Handler
}

func NewConsumer(url, queue string) (*Consumer, error) {
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

	return &Consumer{conn: conn, channel: channel, queue: queue, routes: map[string]Handler{}}, nil
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
	deliveries, err := c.channel.ConsumeWithContext(ctx, c.queue, "", false, false, false, false, nil)
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

func (c *Consumer) dispatch(ctx context.Context, delivery amqp.Delivery) {
	var envelope eventsv1.EventEnvelope
	if err := protojson.Unmarshal(delivery.Body, &envelope); err != nil {
		slog.Error("не разобрали событие", "error", err, "message_id", delivery.MessageId)
		_ = delivery.Nack(false, false)
		return
	}

	// Трасса продолжается: контекст пришёл вместе с событием.
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
		_ = delivery.Ack(false)
		return
	}

	if err := handler(ctx, &envelope); err != nil {
		log.Error("обработка не удалась", "error", err)
		_ = delivery.Nack(false, false)
		return
	}

	log.Debug("обработано")
	_ = delivery.Ack(false)
}
