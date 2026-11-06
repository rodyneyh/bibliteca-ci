"""Formatos de relatório: um formato novo é uma classe nova + uma linha no registro."""

import json
from typing import Protocol


class Formatador(Protocol):
    media_type: str

    def formatar(self, linhas: list[dict]) -> str: ...


class FormatadorJSON:
    media_type = "application/json"

    def formatar(self, linhas: list[dict]) -> str:
        return json.dumps(linhas, ensure_ascii=False)


class FormatadorCSV:
    media_type = "text/csv"

    def formatar(self, linhas: list[dict]) -> str:
        texto = "leitor;livro;prazo;dias_atraso\n"
        for linha in linhas:
            texto += f"{linha['leitor']};{linha['livro']};{linha['prazo']};{linha['dias_atraso']}\n"
        return texto


FORMATADORES: dict[str, Formatador] = {
    "json": FormatadorJSON(),
    "csv": FormatadorCSV(),
}
