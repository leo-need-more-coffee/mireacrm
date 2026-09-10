package infra

import (
	"context"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
	"go.opentelemetry.io/otel/trace"
	"google.golang.org/grpc"
)

// Наблюдаемость: метрики Prometheus и трассировка OpenTelemetry.
//
// Трассировка включается адресом коллектора — пустой адрес означает выключено.
// Метрики работают всегда: их отдача ничего не стоит и ни от чего не зависит.

// Метки должны быть перечислимыми. Путь берётся шаблоном маршрута chi
// (/branches/{branchID}/stock), а не фактическим: иначе каждый идентификатор
// порождает свой временной ряд.
var (
	httpRequests = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Обработанные HTTP-запросы",
		},
		[]string{"service", "method", "route", "status"},
	)
	httpLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Время обработки HTTP-запроса",
			Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5},
		},
		[]string{"service", "method", "route"},
	)
	eventsPublished = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "domain_events_published_total",
			Help: "Опубликованные доменные события",
		},
		[]string{"service", "routing_key"},
	)
	eventsConsumed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "domain_events_consumed_total",
			Help: "Обработанные доменные события",
		},
		[]string{"service", "routing_key", "outcome"},
	)
	grpcRequests = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "grpc_server_requests_total",
			Help: "Обработанные вызовы gRPC",
		},
		[]string{"service", "method", "code"},
	)
)

func init() {
	prometheus.MustRegister(
		httpRequests, httpLatency, eventsPublished, eventsConsumed, grpcRequests)
}

// Пробы и отдача метрик из статистики исключены: они дают постоянный фон
// и смазывают картину нагрузки.
var silentPaths = map[string]bool{"/healthz": true, "/readyz": true, "/metrics": true}

// CountEventPublished и остальные — точки учёта для доменного кода.
func CountEventPublished(service, routingKey string) {
	eventsPublished.WithLabelValues(service, routingKey).Inc()
}

func CountEventConsumed(service, routingKey, outcome string) {
	eventsConsumed.WithLabelValues(service, routingKey, outcome).Inc()
}

func CountGRPC(service, method, code string) {
	grpcRequests.WithLabelValues(service, method, code).Inc()
}

type statusWriter struct {
	http.ResponseWriter
	status int
}

func (w *statusWriter) WriteHeader(code int) {
	w.status = code
	w.ResponseWriter.WriteHeader(code)
}

func (w *statusWriter) Write(b []byte) (int, error) {
	if w.status == 0 {
		w.status = http.StatusOK
	}
	return w.ResponseWriter.Write(b)
}

// MetricsMiddleware считает запросы. Шаблон маршрута доступен только после
// маршрутизации, поэтому метка снимается уже на выходе.
func MetricsMiddleware(service string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if silentPaths[r.URL.Path] {
				next.ServeHTTP(w, r)
				return
			}

			started := time.Now()
			writer := &statusWriter{ResponseWriter: w}
			next.ServeHTTP(writer, r)

			route := chi.RouteContext(r.Context()).RoutePattern()
			if route == "" {
				route = "unmatched"
			}
			if writer.status == 0 {
				writer.status = http.StatusOK
			}
			// Спан создаёт otelhttp снаружи и закрывает уже после нас, поэтому
			// переименовать его в шаблон маршрута можно только здесь: до
			// маршрутизации chi шаблон ещё неизвестен.
			if span := trace.SpanFromContext(r.Context()); span.IsRecording() {
				span.SetName(r.Method + " " + route)
				span.SetAttributes(semconv.HTTPRoute(route))
			}

			httpRequests.WithLabelValues(
				service, r.Method, route, strconv.Itoa(writer.status)).Inc()
			httpLatency.WithLabelValues(
				service, r.Method, route).Observe(time.Since(started).Seconds())
		})
	}
}

func MetricsHandler() http.Handler {
	return promhttp.Handler()
}

// SetupTracing поднимает экспорт трасс по OTLP. Возвращает функцию остановки:
// без неё накопленные спаны теряются при завершении процесса.
func SetupTracing(ctx context.Context, service, endpoint string) (func(context.Context) error, error) {
	if endpoint == "" {
		return func(context.Context) error { return nil }, nil
	}

	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint(endpoint),
		otlptracegrpc.WithInsecure(),
	)
	if err != nil {
		return nil, err
	}

	// Ресурс без схемы: слияние со стандартным падает, если версия
	// семантических соглашений в коде и в SDK разошлась, а имя сервиса —
	// единственный нужный здесь атрибут.
	provider := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewSchemaless(semconv.ServiceName(service))),
	)
	otel.SetTracerProvider(provider)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	return provider.Shutdown, nil
}

// TraceparentFrom отдаёт контекст трассы для конверта события и для метаданных.
// Когда трассировка включена, идентификатор берётся у активного спана: иначе
// трасса в Jaeger и трасса в событиях разъехались бы.
func TraceparentFrom(ctx context.Context) string {
	carrier := propagation.MapCarrier{}
	otel.GetTextMapPropagator().Inject(ctx, carrier)
	if value := carrier.Get(TraceHeader); value != "" {
		return value
	}
	return Traceparent(ctx)
}

// PublishSpan — спан издателя события. Контекст уезжает в самом конверте,
// а не в заголовках AMQP: так его одинаково читают оба языка.
func PublishSpan(ctx context.Context, routingKey string) (context.Context, trace.Span) {
	return otel.Tracer("events").Start(ctx, "publish "+routingKey,
		trace.WithSpanKind(trace.SpanKindProducer),
		trace.WithAttributes(attribute.String("messaging.routing_key", routingKey)))
}

// ConsumeSpan продолжает трассу издателя на другом конце очереди.
func ConsumeSpan(
	ctx context.Context, routingKey, traceparent string,
) (context.Context, trace.Span) {
	if traceparent != "" {
		ctx = otel.GetTextMapPropagator().Extract(
			ctx, propagation.MapCarrier{TraceHeader: traceparent})
	}
	return otel.Tracer("events").Start(ctx, "consume "+routingKey,
		trace.WithSpanKind(trace.SpanKindConsumer),
		trace.WithAttributes(attribute.String("messaging.routing_key", routingKey)))
}

// FailSpan помечает спан неуспешным, чтобы отказ было видно в поиске по трассам.
func FailSpan(span trace.Span, err error) {
	span.RecordError(err)
	span.SetStatus(codes.Error, err.Error())
}

// HTTPHandler оборачивает маршрутизатор трассировкой входящих запросов.
func HTTPHandler(handler http.Handler, service string) http.Handler {
	return otelhttp.NewHandler(handler, service,
		otelhttp.WithFilter(func(r *http.Request) bool { return !silentPaths[r.URL.Path] }))
}

// GRPCServerHandler и GRPCClientHandler связывают трассы через границу gRPC.
func GRPCServerHandler() grpc.ServerOption {
	return grpc.StatsHandler(otelgrpc.NewServerHandler())
}

func GRPCClientHandler() grpc.DialOption {
	return grpc.WithStatsHandler(otelgrpc.NewClientHandler())
}
