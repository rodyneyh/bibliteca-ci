"""Testes unitários das regras e políticas."""

from datetime import date

import pytest

from biblioteca.politicas import POLITICAS
from biblioteca.regras import multa_base, proximo_dia_util


@pytest.mark.parametrize(
    "dia, esperado",
    [
        (date(2026, 10, 30), date(2026, 10, 30)),  # sexta continua sexta
        (date(2026, 10, 31), date(2026, 11, 2)),  # sábado vai para segunda
        (date(2026, 11, 1), date(2026, 11, 2)),  # domingo vai para segunda
    ],
)
def test_proximo_dia_util(dia, esperado):
    assert proximo_dia_util(dia) == esperado


@pytest.mark.parametrize(
    "atraso, esperado",
    [
        (-3, 0.0),
        (0, 0.0),
        (1, 2.0),
        (25, 50.0),
        (100, 50.0),
    ],
)
def test_multa_base(atraso, esperado):
    assert multa_base(atraso) == esperado


def test_estudante_paga_metade_do_teto():
    assert POLITICAS["estudante"].multa(40) == 25.0


def test_limite_padrao_e_3():
    assert POLITICAS["comum"].limite_emprestimos == 3
