package infra

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// ShutdownGrace — сколько ждём завершения текущих запросов при SIGTERM.
const ShutdownGrace = 10 * time.Second

// Env возвращает значение переменной окружения. Пустое значение считается
// незаданным: в compose переменная без значения приезжает пустой строкой,
// и подставить умолчание правильнее, чем стартовать с пустым адресом.
func Env(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok && value != "" {
		return value
	}
	return fallback
}

func EnvInt(key string, fallback int) (int, error) {
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
