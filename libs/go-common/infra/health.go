package infra

import (
	"context"
	"net/http"
	"time"
)

// Проверки разделены: liveness отвечает «процесс не завис», readiness —
// «зависимости доступны». Если их смешать, оркестратор либо считает сервис
// живым при лежащей базе, либо перезапускает его из-за чужого сбоя.

type Probe struct {
	Name  string
	Check func(context.Context) error
}

func LivenessHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		WriteJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	}
}

func ReadinessHandler(probes ...Probe) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()

		checks := make(map[string]string, len(probes))
		ready := true
		for _, probe := range probes {
			if err := probe.Check(ctx); err != nil {
				checks[probe.Name] = "error: " + err.Error()
				ready = false
				continue
			}
			checks[probe.Name] = "ok"
		}

		status := http.StatusOK
		state := "ok"
		if !ready {
			status, state = http.StatusServiceUnavailable, "degraded"
		}
		WriteJSON(w, status, map[string]any{"status": state, "checks": checks})
	}
}
