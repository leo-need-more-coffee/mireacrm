FROM golang:1.26-alpine AS builder

WORKDIR /src

# Контекст сборки — корень репозитория: модуль зависит от gen/go
# через replace-директиву.
COPY gen/go ./gen/go
COPY services/booking-service/go.mod services/booking-service/go.sum ./services/booking-service/
WORKDIR /src/services/booking-service
RUN go mod download

COPY services/booking-service ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/booking ./cmd/booking

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /out/booking /booking
EXPOSE 8003 9003
USER nonroot:nonroot
ENTRYPOINT ["/booking"]
