from dataclasses import dataclass
from datetime import date


@dataclass
class Leitor:
    id: int
    nome: str
    tipo: str
    email: str
    telefone: str | None = None


@dataclass
class Livro:
    id: int
    titulo: str
    disponivel: bool = True


@dataclass
class Emprestimo:
    id: int
    leitor_id: int
    livro_id: int
    data_emprestimo: date
    prazo: date
    devolvido_em: date | None = None
    multa: float | None = None
