package infra

import (
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
)

// TraceMiddleware подхватывает traceparent из запроса или начинает новую трассу
// и возвращает его в ответе, чтобы клиент мог сослаться на неё в логах.
func TraceMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		traceparent := ParseTraceparent(r.Header.Get(TraceHeader))
		w.Header().Set(TraceHeader, traceparent)
		next.ServeHTTP(w, r.WithContext(WithTraceparent(r.Context(), traceparent)))
	})
}

type errorBody struct {
	Detail string `json:"detail"`
}

// WriteError — единственное место, где доменные ошибки превращаются в коды HTTP.
func WriteError(w http.ResponseWriter, r *http.Request, err error) {
	status := http.StatusInternalServerError
	detail := "внутренняя ошибка"

	var notFound *NotFoundError
	var forbidden *ForbiddenError
	var conflict *ConflictError
	var invalid *InvalidArgumentError
	var unavailable *UnavailableError

	switch {
	case errors.As(err, &notFound):
		status, detail = http.StatusNotFound, err.Error()
	case errors.As(err, &forbidden):
		status, detail = http.StatusForbidden, err.Error()
	case errors.As(err, &conflict):
		status, detail = http.StatusConflict, err.Error()
	case errors.As(err, &invalid):
		status, detail = http.StatusUnprocessableEntity, err.Error()
	case errors.As(err, &unavailable):
		status, detail = http.StatusServiceUnavailable, err.Error()
		slog.WarnContext(r.Context(), "сосед недоступен",
			"dependency", unavailable.Dependency, "error", unavailable.Err,
			"trace_id", TraceID(Traceparent(r.Context())))
	default:
		slog.ErrorContext(r.Context(), "необработанная ошибка",
			"error", err, "trace_id", TraceID(Traceparent(r.Context())))
	}

	WriteJSON(w, status, errorBody{Detail: detail})
}

func WriteJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if payload != nil {
		_ = json.NewEncoder(w).Encode(payload)
	}
}
