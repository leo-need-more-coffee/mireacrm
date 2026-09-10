package infra

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	ServiceName  string
	HTTPPort     int
	GRPCPort     int
	AMQPURL      string
	NATSURL      string
	ClientAddr   string
	OTLPEndpoint string
	Debug        bool
}

func LoadConfig() (Config, error) {
	cfg := Config{
		ServiceName: "notification-service",
		AMQPURL:     env("NOTIFICATION_AMQP_URL", "amqp://guest:guest@localhost:5672/"),
		NATSURL:     env("NOTIFICATION_NATS_URL", "nats://localhost:4222"),
		ClientAddr:  env("NOTIFICATION_CLIENT_ADDR", "localhost:9005"),
		// Пустой адрес выключает экспорт трасс.
		OTLPEndpoint: env("NOTIFICATION_OTLP_ENDPOINT", ""),
		Debug:        env("NOTIFICATION_DEBUG", "false") == "true",
	}

	var err error
	if cfg.HTTPPort, err = envInt("NOTIFICATION_HTTP_PORT", 8007); err != nil {
		return cfg, err
	}
	if cfg.GRPCPort, err = envInt("NOTIFICATION_GRPC_PORT", 9007); err != nil {
		return cfg, err
	}
	return cfg, nil
}

// ShutdownGrace — сколько ждём завершения текущих запросов при SIGTERM.
const ShutdownGrace = 10 * time.Second

func env(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok && value != "" {
		return value
	}
	return fallback
}

func envInt(key string, fallback int) (int, error) {
	raw, ok := os.LookupEnv(key)
	if !ok || raw == "" {
		return fallback, nil
	}
	value, err := strconv.Atoi(raw)
	if err != nil {
		return 0, fmt.Errorf("%s: %w", key, err)
	}
	return value, nil
}
