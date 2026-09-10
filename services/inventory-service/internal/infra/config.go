package infra

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	ServiceName  string
	PostgresDSN  string
	HTTPPort     int
	GRPCPort     int
	AMQPURL      string
	NATSURL      string
	CatalogAddr  string
	OTLPEndpoint string
	Debug        bool
}

func LoadConfig() (Config, error) {
	cfg := Config{
		ServiceName: "inventory-service",
		PostgresDSN: env("INVENTORY_POSTGRES_DSN", "postgres://inventory_user:inventory_pass@localhost:5432/inventory_db"),
		AMQPURL:     env("INVENTORY_AMQP_URL", "amqp://guest:guest@localhost:5672/"),
		NATSURL:     env("INVENTORY_NATS_URL", "nats://localhost:4222"),
		CatalogAddr: env("INVENTORY_CATALOG_ADDR", "localhost:9002"),
		// Пустой адрес выключает экспорт трасс.
		OTLPEndpoint: env("INVENTORY_OTLP_ENDPOINT", ""),
		Debug:        env("INVENTORY_DEBUG", "false") == "true",
	}

	var err error
	if cfg.HTTPPort, err = envInt("INVENTORY_HTTP_PORT", 8004); err != nil {
		return cfg, err
	}
	if cfg.GRPCPort, err = envInt("INVENTORY_GRPC_PORT", 9004); err != nil {
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
