package infra

import "fmt"

// Доменные ошибки. Каждый транспорт маппит их в свои коды: HTTP — в
// internal/api, gRPC — перехватчиком в rpcserver.go.

type NotFoundError struct {
	What string
	Key  any
}

func (e *NotFoundError) Error() string { return fmt.Sprintf("%s %v не найден", e.What, e.Key) }

func NotFound(what string, key any) error { return &NotFoundError{What: what, Key: key} }

type ConflictError struct{ Reason string }

func (e *ConflictError) Error() string { return e.Reason }

func Conflict(format string, args ...any) error {
	return &ConflictError{Reason: fmt.Sprintf(format, args...)}
}

type InvalidArgumentError struct{ Reason string }

func (e *InvalidArgumentError) Error() string { return e.Reason }

func InvalidArgument(format string, args ...any) error {
	return &InvalidArgumentError{Reason: fmt.Sprintf(format, args...)}
}

// ForbiddenError — роли достаточно, но объект принадлежит другому сотруднику.
type ForbiddenError struct{ What string }

func (e *ForbiddenError) Error() string {
	return e.What + ": доступ только к своим записям"
}

func Forbidden(what string) error { return &ForbiddenError{What: what} }

// UnavailableError — сосед недоступен. Не наша поломка, поэтому 503, а не 500:
// клиенту имеет смысл повторить запрос.
type UnavailableError struct {
	Dependency string
	Err        error
}

func (e *UnavailableError) Error() string { return e.Dependency + " недоступен" }

func (e *UnavailableError) Unwrap() error { return e.Err }

func Unavailable(dependency string, err error) error {
	return &UnavailableError{Dependency: dependency, Err: err}
}
