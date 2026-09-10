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
	caller := callerFromHeaders("", "", "admin,manager", "someone")
	if caller.Known() || len(caller.Roles) != 0 || caller.EmployeeID != "" {
		t.Errorf("личность без идентификатора не должна приниматься: %+v", caller)
	}
}

func TestOwnership(t *testing.T) {
	const own = "3a7c9d21-0000-4000-8000-0000000000aa"
	const other = "3a7c9d21-0000-4000-8000-0000000000bb"

	cases := []struct {
		name    string
		caller  Caller
		owner   string
		allowed bool
	}{
		{"специалист со своим объектом",
			Caller{Subject: "s", Roles: []string{"specialist"}, EmployeeID: own}, own, true},
		{"специалист с чужим объектом",
			Caller{Subject: "s", Roles: []string{"specialist"}, EmployeeID: own}, other, false},
		{"управляющий с чужим объектом",
			Caller{Subject: "m", Roles: []string{"manager"}, EmployeeID: ""}, other, true},
		{"специалист без привязки к сотруднику",
			Caller{Subject: "s", Roles: []string{"specialist"}}, other, false},
		{"вызов изнутри системы, без личности",
			Caller{}, other, true},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			err := EnsureOwner(c.caller, c.owner, "визит")
			if c.allowed && err != nil {
				t.Errorf("ожидался доступ, получено: %v", err)
			}
			if !c.allowed && err == nil {
				t.Error("ожидался отказ, доступ разрешён")
			}
		})
	}
}
