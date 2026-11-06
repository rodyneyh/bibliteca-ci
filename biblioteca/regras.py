"""Regras que valem para todos os leitores."""

from datetime import date, timedelta

MULTA_POR_DIA = 2.00
MULTA_MAXIMA = 50.00


def proximo_dia_util(dia: date) -> date:
    """Sábado e domingo passam para a segunda-feira seguinte."""
    if dia.weekday() == 5:
        return dia + timedelta(days=2)
    if dia.weekday() == 6:
        return dia + timedelta(days=1)
    return dia


def multa_base(dias_atraso: int) -> float:
    if dias_atraso <= 0:
        return 0.0
    return min(dias_atraso * MULTA_POR_DIA, MULTA_MAXIMA)
