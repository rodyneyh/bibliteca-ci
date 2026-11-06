"""O que muda de um tipo de leitor para outro.

Aberto/Fechado: um tipo novo é uma classe nova + uma linha no registro.
Nenhuma regra existente precisa ser editada.
"""

from datetime import date, timedelta

from biblioteca.regras import multa_base, proximo_dia_util


class PoliticaLeitor:
    prazo_dias = 14
    limite_emprestimos = 3

    def prazo(self, data_emprestimo: date) -> date:
        return proximo_dia_util(data_emprestimo + timedelta(days=self.prazo_dias))

    def multa(self, dias_atraso: int) -> float:
        return multa_base(dias_atraso)


class LeitorComum(PoliticaLeitor):
    pass


class LeitorEstudante(PoliticaLeitor):
    def multa(self, dias_atraso: int) -> float:
        return super().multa(dias_atraso) * 0.5


POLITICAS: dict[str, PoliticaLeitor] = {
    "comum": LeitorComum(),
    "estudante": LeitorEstudante(),
}
