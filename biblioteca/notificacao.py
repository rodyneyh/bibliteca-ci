"""Canais de notificação.

Inversão de dependência: o serviço conhece só o contrato `Notificador`,
não sabe se a mensagem vai por e-mail, SMS ou pombo-correio.
"""

from typing import Protocol

from biblioteca.modelos import Leitor


class Notificador(Protocol):
    def enviar(self, leitor: Leitor, assunto: str, corpo: str) -> None: ...


class CaixaDeSaida:
    """Simula os gateways: guarda o que teria sido enviado."""

    def __init__(self):
        self.mensagens: list[dict] = []

    def registrar(self, canal: str, para: str, assunto: str, corpo: str):
        self.mensagens.append({"canal": canal, "para": para, "assunto": assunto, "corpo": corpo})


class NotificadorEmail:
    def __init__(self, caixa: CaixaDeSaida):
        self.caixa = caixa

    def enviar(self, leitor: Leitor, assunto: str, corpo: str) -> None:
        self.caixa.registrar("email", leitor.email, assunto, corpo)
