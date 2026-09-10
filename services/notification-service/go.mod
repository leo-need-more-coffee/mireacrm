module mirea-crm/services/notification-service

go 1.26.0

replace mirea-crm/gen/go => ../../gen/go

require (
	github.com/go-chi/chi/v5 v5.3.2
	github.com/google/uuid v1.6.0
	github.com/nats-io/nats.go v1.53.1
	github.com/rabbitmq/amqp091-go v1.14.0
	google.golang.org/grpc v1.83.2
	google.golang.org/protobuf v1.36.12
	mirea-crm/gen/go v0.0.0-00010101000000-000000000000
)

require (
	github.com/klauspost/compress v1.18.5 // indirect
	github.com/nats-io/nkeys v0.4.15 // indirect
	github.com/nats-io/nuid v1.0.1 // indirect
	golang.org/x/crypto v0.55.0 // indirect
	golang.org/x/net v0.58.0 // indirect
	golang.org/x/sys v0.47.0 // indirect
	golang.org/x/text v0.41.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20260526163538-3dc84a4a5aaa // indirect
)
