"""Расчёт баллов лояльности."""

import pytest

from app.domain import points_for


@pytest.mark.parametrize(
    ("paid_kopecks", "expected"),
    [
        (0, 0),
        (100_00, 5),        # 100 руб → 5 баллов
        (5_200_00, 260),    # окрашивание за 5200 руб
        (99, 0),            # меньше рубля — баллов нет
        (1_99, 0),          # округление вниз: 1.99 руб → 0.0995 балла
    ],
)
def test_points_calculation(paid_kopecks: int, expected: int):
    assert points_for(paid_kopecks) == expected


def test_points_never_negative():
    assert points_for(0) == 0
