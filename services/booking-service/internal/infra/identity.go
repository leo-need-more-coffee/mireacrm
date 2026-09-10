package infra

import (
	"context"
	"net/http"
	"net/url"
	"strings"

	"google.golang.org/grpc/metadata"
)

// Личность вызывающего, разобранная шлюзом. Токен проверяется один раз на входе,
// дальше по системе едет результат: иначе внутренняя сеть доверенная целиком.
//
// Имя кодируется процентами — и заголовок HTTP, и метаданные gRPC допускают
// только ASCII, а имя пользователя может оказаться кириллицей.

const (
	HeaderSubject  = "x-user-id"
	HeaderUsername = "x-user-name"
	HeaderRoles    = "x-user-roles"
	HeaderEmployee = "x-employee-id"
)

// Роли, которым видно чужое. Специалист работает только со своим.
var privilegedRoles = []string{"admin", "manager"}

type Caller struct {
	Subject    string
	Username   string
	Roles      []string
	EmployeeID string
}

func (c Caller) Known() bool { return c.Subject != "" }

func (c Caller) Privileged() bool { return c.HasAny(privilegedRoles...) }

func (c Caller) HasAny(roles ...string) bool {
	for _, own := range c.Roles {
		for _, wanted := range roles {
			if own == wanted {
				return true
			}
		}
	}
	return false
}

type callerKey struct{}

func WithCaller(ctx context.Context, caller Caller) context.Context {
	return context.WithValue(ctx, callerKey{}, caller)
}

func CallerFrom(ctx context.Context) Caller {
	caller, _ := ctx.Value(callerKey{}).(Caller)
	return caller
}

func callerFromHeaders(subject, username, roles, employee string) Caller {
	if subject == "" {
		return Caller{}
	}
	name, err := url.QueryUnescape(username)
	if err != nil {
		name = username
	}
	caller := Caller{Subject: subject, Username: name, EmployeeID: employee}
	for _, role := range strings.Split(roles, ",") {
		if role = strings.TrimSpace(role); role != "" {
			caller.Roles = append(caller.Roles, role)
		}
	}
	return caller
}

// IdentityMiddleware вносит личность из заголовков шлюза в контекст запроса.
func IdentityMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		caller := callerFromHeaders(
			r.Header.Get(HeaderSubject),
			r.Header.Get(HeaderUsername),
			r.Header.Get(HeaderRoles),
			r.Header.Get(HeaderEmployee),
		)
		next.ServeHTTP(w, r.WithContext(WithCaller(r.Context(), caller)))
	})
}

func callerFromMetadata(md metadata.MD) Caller {
	first := func(key string) string {
		if values := md.Get(key); len(values) > 0 {
			return values[0]
		}
		return ""
	}
	return callerFromHeaders(
		first(HeaderSubject), first(HeaderUsername), first(HeaderRoles), first(HeaderEmployee))
}

// Outgoing собирает метаданные для вызова соседа: трасса и личность.
func Outgoing(ctx context.Context) context.Context {
	pairs := make([]string, 0, 8)
	if traceparent := Traceparent(ctx); traceparent != "" {
		pairs = append(pairs, TraceHeader, traceparent)
	}
	if caller := CallerFrom(ctx); caller.Known() {
		pairs = append(pairs,
			HeaderSubject, caller.Subject,
			HeaderUsername, url.QueryEscape(caller.Username),
			HeaderRoles, strings.Join(caller.Roles, ","),
			HeaderEmployee, caller.EmployeeID,
		)
	}
	if len(pairs) == 0 {
		return ctx
	}
	return metadata.AppendToOutgoingContext(ctx, pairs...)
}

// EnsureOwner пропускает вызов, если объект принадлежит вызывающему.
//
// Роль проверяет шлюз, принадлежность — сервис-владелец: только он знает, чей
// это объект. Вызов без личности — обращение изнутри системы, а не от
// человека: потребитель события или служебная задача. Снаружи такой вызов не
// сделать, заголовки личности шлюз затирает.
func EnsureOwner(caller Caller, ownerID, what string) error {
	if !caller.Known() || caller.Privileged() {
		return nil
	}
	// Пустая привязка означает, что учётной записи не соответствует ни один
	// сотрудник. Отказ по умолчанию: иначе такая учётка видела бы всё.
	if caller.EmployeeID == "" || caller.EmployeeID != ownerID {
		return Forbidden(what)
	}
	return nil
}
