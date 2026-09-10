package main

import (
	"context"
	"errors"
	"flag"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/google/uuid"

	eventsv1 "mirea-crm/gen/go/mirea/events/v1"

	"mirea-crm/services/inventory-service/internal/api"
	"mirea-crm/services/inventory-service/internal/clients"
	"mirea-crm/services/inventory-service/internal/infra"
	"mirea-crm/services/inventory-service/internal/inventory"
	"mirea-crm/services/inventory-service/migrations"
)

const queueName = "inventory-service.events"

func main() {
	// В distroless-образе нет ни shell, ни curl, поэтому healthcheck
	// контейнера выполняет сам бинарник.
	healthcheck := flag.Bool("healthcheck", false, "проверить готовность и выйти")
	flag.Parse()
	if *healthcheck {
		os.Exit(probe())
	}

	if err := run(); err != nil {
		slog.Error("сервис остановлен с ошибкой", "error", err)
		os.Exit(1)
	}
}

func run() error {
	cfg, err := infra.LoadConfig()
	if err != nil {
		return err
	}
	setupLogging(cfg.Debug)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if err := infra.Migrate(ctx, cfg.PostgresDSN, migrations.Files); err != nil {
		return err
	}
	slog.Info("миграции накачены")

	pool, err := infra.NewPool(ctx, cfg.PostgresDSN)
	if err != nil {
		return err
	}
	defer pool.Close()

	catalog, err := clients.DialCatalog(cfg.CatalogAddr)
	if err != nil {
		return err
	}
	defer catalog.Close()

	events, err := infra.NewEventPublisher(cfg.AMQPURL, cfg.ServiceName)
	if err != nil {
		return err
	}
	defer events.Close()

	realtime, err := infra.NewRealtimePublisher(cfg.NATSURL, cfg.ServiceName)
	if err != nil {
		return err
	}
	defer realtime.Close()

	service := inventory.New(inventory.NewRepository(pool), catalog, events, realtime)

	consumer, err := infra.NewConsumer(cfg.AMQPURL, queueName)
	if err != nil {
		return err
	}
	defer consumer.Close()
	consumer.Handle("appointment.completed", writeOffHandler(service))

	router := api.NewRouter(service,
		infra.Probe{Name: "database", Check: pool.Ping},
		infra.Probe{Name: "broker", Check: events.Ping},
		infra.Probe{Name: "realtime", Check: realtime.Ping},
	)
	server := &http.Server{Addr: ":" + strconv.Itoa(cfg.HTTPPort), Handler: router}

	errc := make(chan error, 2)
	go func() {
		slog.Info("HTTP слушает", "port", cfg.HTTPPort)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errc <- err
		}
	}()
	go func() {
		if err := consumer.Run(ctx); err != nil {
			errc <- err
		}
	}()

	select {
	case err := <-errc:
		return err
	case <-ctx.Done():
		slog.Info("получен сигнал, останавливаемся")
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), infra.ShutdownGrace)
	defer cancel()
	return server.Shutdown(shutdownCtx)
}

// writeOffHandler превращает событие в доменную операцию. Разбор payload —
// работа транспорта, домен получает уже готовые идентификаторы.
func writeOffHandler(service *inventory.Service) infra.Handler {
	return func(ctx context.Context, envelope *eventsv1.EventEnvelope) error {
		payload := envelope.GetAppointmentCompleted()
		if payload == nil {
			return errors.New("appointment.completed без payload")
		}

		eventID, err := uuid.Parse(envelope.GetEventId())
		if err != nil {
			return err
		}
		appointmentID, err := uuid.Parse(payload.GetAppointmentId())
		if err != nil {
			return err
		}
		branchID, err := uuid.Parse(payload.GetBranchId())
		if err != nil {
			return err
		}
		serviceID, err := uuid.Parse(payload.GetServiceId())
		if err != nil {
			return err
		}

		return service.WriteOffForAppointment(ctx, eventID, appointmentID, branchID, serviceID)
	}
}

func probe() int {
	cfg, err := infra.LoadConfig()
	if err != nil {
		return 1
	}

	client := http.Client{Timeout: 3 * time.Second}
	response, err := client.Get("http://127.0.0.1:" + strconv.Itoa(cfg.HTTPPort) + "/readyz")
	if err != nil {
		return 1
	}
	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		return 1
	}
	return 0
}

func setupLogging(debug bool) {
	level := slog.LevelInfo
	if debug {
		level = slog.LevelDebug
	}
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: level})))
}
