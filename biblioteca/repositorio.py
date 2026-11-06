"""Armazenamento em memória. Trocar por um banco não muda o serviço."""

from biblioteca.modelos import Emprestimo, Leitor, Livro

TITULOS = [
    "Dom Casmurro",
    "O Cortiço",
    "Vidas Secas",
    "Memórias Póstumas de Brás Cubas",
    "Grande Sertão: Veredas",
    "A Hora da Estrela",
    "Capitães da Areia",
]


class RepositorioMemoria:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.leitores: dict[int, Leitor] = {
            1: Leitor(1, "Ana", "comum", "ana@exemplo.com"),
            2: Leitor(2, "Bruno", "estudante", "bruno@exemplo.com", "+5511999990002"),
        }
        self.livros: dict[int, Livro] = {i: Livro(i, t) for i, t in enumerate(TITULOS, start=1)}
        self.emprestimos: dict[int, Emprestimo] = {}

    def salvar_leitor(self, leitor: Leitor) -> Leitor:
        leitor.id = max(self.leitores, default=0) + 1
        self.leitores[leitor.id] = leitor
        return leitor

    def salvar_emprestimo(self, emprestimo: Emprestimo) -> Emprestimo:
        emprestimo.id = max(self.emprestimos, default=0) + 1
        self.emprestimos[emprestimo.id] = emprestimo
        return emprestimo

    def ativos_do_leitor(self, leitor_id: int) -> int:
        return sum(
            1
            for e in self.emprestimos.values()
            if e.leitor_id == leitor_id and e.devolvido_em is None
        )

    def atrasados(self, hoje) -> list[Emprestimo]:
        return [e for e in self.emprestimos.values() if e.devolvido_em is None and e.prazo < hoje]
