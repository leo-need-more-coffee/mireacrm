package infra

import (
	"context"
	"testing"

	"google.golang.org/grpc/metadata"
)

func TestCallerSurvivesGRPCHop(t *testing.T) {
	caller := Caller{
		Subject:  "8f1c0e4e-0000-4000-8000-000000000001",
		Username: "Ольга Владелец",
		Roles:    []string{"admin", "manager"},
	}

	ctx := Outgoing(WithCaller(context.Background(), caller))
	outgoing, ok := metadata.FromOutgoingContext(ctx)
	if !ok {
		t.Fatal("метаданные не выставлены")
	}

	got := callerFromMetadata(outgoing)
	if got.Subject != caller.Subject {
		t.Errorf("subject: %q, ожидался %q", got.Subject, caller.Subject)
	}
	// Кириллица в метаданных gRPC запрещена, поэтому имя едет закодированным.
	if got.Username != caller.Username {
		t.Errorf("username: %q, ожидалось %q", got.Username, caller.Username)
	}
	if !got.HasAny("manager") || got.HasAny("specialist") {
		t.Errorf("роли разобраны неверно: %v", got.Roles)
	}
}

func TestUnknownCallerAddsNothing(t *testing.T) {
	ctx := Outgoing(WithTraceparent(context.Background(), NewTraceparent()))
	outgoing, _ := metadata.FromOutgoingContext(ctx)
	if values := outgoing.Get(HeaderSubject); len(values) != 0 {
		t.Errorf("пустая личность не должна попадать в метаданные: %v", values)
	}
}

func TestForgedRolesWithoutSubjectIgnored(t *testing.T) {
	caller := callerFromHeaders("", "", "admin,manager")
	if caller.Known() || len(caller.Roles) != 0 {
		t.Errorf("роли без идентификатора не должны приниматься: %+v", caller)
	}
}
