package infra

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/nats-io/nats.go"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
)

// RealtimePublisher шлёт эфемерные сообщения в NATS: живое табло занятости.
// Гарантий доставки нет и не нужно — сообщение устаревает за секунды,
// подписчик ресинкнется при переподключении. Всё надёжное идёт в RabbitMQ.
type RealtimePublisher struct {
	conn *nats.Conn
}

func NewRealtimePublisher(url, name string) (*RealtimePublisher, error) {
	conn, err := nats.Connect(url,
		nats.Name(name),
		nats.MaxReconnects(-1),
	)
	if err != nil {
		return nil, fmt.Errorf("подключение к NATS: %w", err)
	}
	slog.Info("подключён к NATS", "url", url)
	return &RealtimePublisher{conn: conn}, nil
}

func (p *RealtimePublisher) Close() {
	if p.conn != nil {
		p.conn.Close()
	}
}

func (p *RealtimePublisher) Publish(ctx context.Context, subject string, message proto.Message) error {
	body, err := protojson.Marshal(message)
	if err != nil {
		return fmt.Errorf("сериализация: %w", err)
	}
	if err := p.conn.Publish(subject, body); err != nil {
		return fmt.Errorf("публикация в %s: %w", subject, err)
	}
	slog.DebugContext(ctx, "отправлено в NATS", "subject", subject)
	return nil
}

func (p *RealtimePublisher) Ping(context.Context) error {
	if p.conn == nil || !p.conn.IsConnected() {
		return fmt.Errorf("нет соединения")
	}
	return nil
}
