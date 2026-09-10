FROM golang:1.26-alpine AS builder

WORKDIR /src

# Контекст сборки — корень репозитория: модуль зависит от gen/go
# и от общего обвяза libs/go-common через replace-директивы.
COPY gen/go ./gen/go
COPY libs/go-common ./libs/go-common
COPY services/notification-service/go.mod services/notification-service/go.sum ./services/notification-service/
WORKDIR /src/services/notification-service
RUN go mod download

COPY services/notification-service ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/notification ./cmd/notification

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /out/notification /notification
EXPOSE 8007
USER nonroot:nonroot
ENTRYPOINT ["/notification"]
