package infra

import (
	"context"
	"errors"
	"log/slog"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"
)

// Registration — как подключить сервисер к серверу.
type Registration func(*grpc.Server)

// ServerInterceptor подхватывает трассу из метаданных и маппит доменные ошибки
// в коды gRPC. Благодаря ему в методах сервисера нет ни одного switch по ошибкам.
func ServerInterceptor(
	ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler,
) (any, error) {
	traceparent := ""
	if md, ok := metadata.FromIncomingContext(ctx); ok {
		if values := md.Get(TraceHeader); len(values) > 0 {
			traceparent = values[0]
		}
		ctx = WithCaller(ctx, callerFromMetadata(md))
	}
	ctx = WithTraceparent(ctx, ParseTraceparent(traceparent))

	response, err := handler(ctx, req)
	if err == nil {
		return response, nil
	}
	return nil, toStatus(ctx, info.FullMethod, err)
}

func toStatus(ctx context.Context, method string, err error) error {
	var notFound *NotFoundError
	var forbidden *ForbiddenError
	var conflict *ConflictError
	var invalid *InvalidArgumentError
	var unavailable *UnavailableError

	switch {
	case errors.As(err, &notFound):
		return status.Error(codes.NotFound, err.Error())
	case errors.As(err, &forbidden):
		return status.Error(codes.PermissionDenied, err.Error())
	case errors.As(err, &conflict):
		return status.Error(codes.Aborted, err.Error())
	case errors.As(err, &invalid):
		return status.Error(codes.InvalidArgument, err.Error())
	case errors.As(err, &unavailable):
		return status.Error(codes.Unavailable, err.Error())
	default:
		slog.ErrorContext(ctx, "необработанная ошибка в gRPC",
			"method", method, "error", err,
			"trace_id", TraceID(Traceparent(ctx)))
		return status.Error(codes.Internal, "внутренняя ошибка")
	}
}

func NewGRPCServer(registrations ...Registration) *grpc.Server {
	server := grpc.NewServer(grpc.UnaryInterceptor(ServerInterceptor))
	for _, register := range registrations {
		register(server)
	}
	// Рефлексия нужна, чтобы grpcurl работал без .proto под рукой.
	reflection.Register(server)
	return server
}
