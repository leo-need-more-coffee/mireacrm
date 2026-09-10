FROM golang:1.26-alpine AS builder

WORKDIR /src

# Контекст сборки — корень репозитория: модуль зависит от gen/go
# и от общего обвяза libs/go-common через replace-директивы.
COPY gen/go ./gen/go
COPY libs/go-common ./libs/go-common
COPY services/inventory-service/go.mod services/inventory-service/go.sum ./services/inventory-service/
WORKDIR /src/services/inventory-service
RUN go mod download

COPY services/inventory-service ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/inventory ./cmd/inventory

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /out/inventory /inventory
EXPOSE 8004
USER nonroot:nonroot
ENTRYPOINT ["/inventory"]
