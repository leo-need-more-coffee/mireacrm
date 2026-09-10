package infra

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"regexp"
)

// Контекст трассировки W3C. Полноценный OpenTelemetry придёт на ПР10, пока —
// минимум, который не даёт трассе рваться на границе брокера.

const TraceHeader = "traceparent"

var traceFormat = regexp.MustCompile(`^[0-9a-f]{2}-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$`)

type traceKey struct{}

func NewTraceparent() string {
	buf := make([]byte, 24)
	_, _ = rand.Read(buf)
	return "00-" + hex.EncodeToString(buf[:16]) + "-" + hex.EncodeToString(buf[16:]) + "-01"
}

// ParseTraceparent принимает валидный заголовок, иначе начинает новую трассу:
// чужой мусор не повод ронять запрос.
func ParseTraceparent(raw string) string {
	if traceFormat.MatchString(raw) {
		return raw
	}
	return NewTraceparent()
}

func WithTraceparent(ctx context.Context, value string) context.Context {
	return context.WithValue(ctx, traceKey{}, value)
}

func Traceparent(ctx context.Context) string {
	value, _ := ctx.Value(traceKey{}).(string)
	return value
}

func TraceID(traceparent string) string {
	if !traceFormat.MatchString(traceparent) {
		return ""
	}
	return traceparent[3:35]
}
