package infra

import (
	"context"
	"fmt"
	"log/slog"

	"github.com/nats-io/nats.go"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
)

// Subscriber читает эфемерные сообщения NATS. Гарантий доставки нет и не нужно:
// сообщение устаревает за секунды, а всё надёжное дублируется через RabbitMQ.
type Subscriber struct {
	conn *nats.Conn
	subs []*nats.Subscription
}

func NewSubscriber(url, name string) (*Subscriber, error) {
	conn, err := nats.Connect(url, nats.Name(name), nats.MaxReconnects(-1))
	if err != nil {
		return nil, fmt.Errorf("подключение к NATS: %w", err)
	}
	slog.Info("подключён к NATS", "url", url)
	return &Subscriber{conn: conn}, nil
}

func (s *Subscriber) Close() {
	for _, sub := range s.subs {
		_ = sub.Unsubscribe()
	}
	if s.conn != nil {
		s.conn.Close()
	}
}

// Subscribe разбирает сообщение в переданный тип и вызывает обработчик.
// Ошибка разбора только логируется: ронять подписку из-за одного мусорного
// сообщения нельзя.
func (s *Subscriber) Subscribe(
	subject string, factory func() proto.Message, handler func(context.Context, proto.Message),
) error {
	sub, err := s.conn.Subscribe(subject, func(msg *nats.Msg) {
		message := factory()
		if err := protojson.Unmarshal(msg.Data, message); err != nil {
			slog.Warn("не разобрали сообщение NATS", "subject", msg.Subject, "error", err)
			return
		}
		handler(context.Background(), message)
	})
	if err != nil {
		return fmt.Errorf("подписка на %s: %w", subject, err)
	}

	s.subs = append(s.subs, sub)
	slog.Info("подписаны на NATS", "subject", subject)
	return nil
}

func (s *Subscriber) Ping(context.Context) error {
	if s.conn == nil || !s.conn.IsConnected() {
		return fmt.Errorf("нет соединения")
	}
	return nil
}
