package infra

import (
	"context"
	"database/sql"
	"fmt"
	"io/fs"

	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/pressly/goose/v3"
)

// Migrate накатывает миграции из встроенной файловой системы: отдельный
// бинарник и монтирование каталога в контейнер не нужны.
func Migrate(ctx context.Context, dsn string, files fs.FS) error {
	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return fmt.Errorf("подключение для миграций: %w", err)
	}
	defer db.Close()

	goose.SetBaseFS(files)
	goose.SetLogger(goose.NopLogger())
	if err := goose.SetDialect("postgres"); err != nil {
		return err
	}
	if err := goose.UpContext(ctx, db, "."); err != nil {
		return fmt.Errorf("накат миграций: %w", err)
	}
	return nil
}
