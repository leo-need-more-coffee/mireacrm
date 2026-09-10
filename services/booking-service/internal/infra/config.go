package infra

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	ServiceName string
	PostgresDSN string
	HTTPPort    int
	GRPCPort    int
	AMQPURL     string
	NATSURL     string
	CoreAddr    string
	CatalogAddr string
	Debug       bool
}

func LoadConfig() (Config, error) {
	cfg := Config{
		ServiceName: "booking-service",
		PostgresDSN: env("BOOKING_POSTGRES_DSN", "postgres://booking_user:booking_pass@localhost:5432/booking_db"),
		AMQPURL:     env("BOOKING_AMQP_URL", "amqp://guest:guest@localhost:5672/"),
		NATSURL:     env("BOOKING_NATS_URL", "nats://localhost:4222"),
		CoreAddr:    env("BOOKING_CORE_ADDR", "localhost:9001"),
		CatalogAddr: env("BOOKING_CATALOG_ADDR", "localhost:9002"),
		Debug:       env("BOOKING_DEBUG", "false") == "true",
	}

	var err error
	if cfg.HTTPPort, err = envInt("BOOKING_HTTP_PORT", 8003); err != nil {
		return cfg, err
	}
	if cfg.GRPCPort, err = envInt("BOOKING_GRPC_PORT", 9003); err != nil {
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
