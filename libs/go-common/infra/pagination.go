package infra

import (
	"encoding/base64"
	"strings"

	"github.com/google/uuid"
)

// Курсорная пагинация. Смещения не используем: списки пополняются во время
// листания, и offset начинает пропускать записи.

const cursorSeparator = "\x00"

func EncodeCursor(sortKey string, id uuid.UUID) string {
	return base64.URLEncoding.EncodeToString([]byte(sortKey + cursorSeparator + id.String()))
}

func DecodeCursor(cursor string) (string, uuid.UUID, error) {
	raw, err := base64.URLEncoding.DecodeString(cursor)
	if err != nil {
		return "", uuid.Nil, InvalidArgument("некорректный курсор")
	}

	sortKey, rawID, found := strings.Cut(string(raw), cursorSeparator)
	if !found {
		return "", uuid.Nil, InvalidArgument("некорректный курсор")
	}

	id, err := uuid.Parse(rawID)
	if err != nil {
		return "", uuid.Nil, InvalidArgument("некорректный курсор")
	}
	return sortKey, id, nil
}
