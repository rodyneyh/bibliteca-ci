"""Casos de uso. Cada classe tem um motivo para mudar."""

from datetime import date

from biblioteca.erros import ErroBiblioteca
from biblioteca.modelos import Emprestimo, Leitor
from biblioteca.notificacao import Notificador
from biblioteca.politicas import PoliticaLeitor
from biblioteca.relatorios import Formatador
from biblioteca.repositorio import RepositorioMemoria


class ServicoLeitores:
    def __init__(self, repo: RepositorioMemoria, politicas: dict[str, PoliticaLeitor]):
        self.repo = repo
        self.politicas = politicas

    def cadastrar(self, nome: str, tipo: str, email: str, telefone: str | None) -> Leitor:
        if tipo not in self.politicas:
            raise ErroBiblioteca(422, "tipo_invalido", "Tipo de leitor inválido")
        if "@" not in email:
            raise ErroBiblioteca(422, "email_invalido", "E-mail inválido")
        return self.repo.salvar_leitor(Leitor(0, nome, tipo, email, telefone))


class ServicoEmprestimos:
    def __init__(
        self,
        repo: RepositorioMemoria,
        politicas: dict[str, PoliticaLeitor],
        notificadores: list[Notificador],
    ):
        self.repo = repo
        self.politicas = politicas
        self.notificadores = notificadores

    def _notificar(self, leitor: Leitor, assunto: str, corpo: str):
        for notificador in self.notificadores:
            notificador.enviar(leitor, assunto, corpo)

    def emprestar(self, leitor_id: int, livro_id: int, hoje: date) -> Emprestimo:
        leitor = self.repo.leitores.get(leitor_id)
        if leitor is None:
            raise ErroBiblioteca(404, "leitor_nao_encontrado", "Leitor não encontrado")
        livro = self.repo.livros.get(livro_id)
        if livro is None:
            raise ErroBiblioteca(404, "livro_nao_encontrado", "Livro não encontrado")
        if not livro.disponivel:
            raise ErroBiblioteca(409, "livro_indisponivel", "Livro já está emprestado")

        politica = self.politicas[leitor.tipo]
        if self.repo.ativos_do_leitor(leitor.id) >= politica.limite_emprestimos:
            raise ErroBiblioteca(409, "limite_excedido", "Leitor atingiu o limite de empréstimos")

        emprestimo = self.repo.salvar_emprestimo(
            Emprestimo(0, leitor.id, livro.id, hoje, politica.prazo(hoje))
        )
        livro.disponivel = False
        self._notificar(
            leitor,
            "Empréstimo confirmado",
            f'Olá, {leitor.nome}! Você pegou "{livro.titulo}". '
            f"Devolva até {emprestimo.prazo.strftime('%d/%m/%Y')}.",
        )
        return emprestimo

    def devolver(self, emprestimo_id: int, hoje: date) -> Emprestimo:
        emprestimo = self.repo.emprestimos.get(emprestimo_id)
        if emprestimo is None:
            raise ErroBiblioteca(404, "emprestimo_nao_encontrado", "Empréstimo não encontrado")
        if emprestimo.devolvido_em is not None:
            raise ErroBiblioteca(409, "ja_devolvido", "Este empréstimo já foi devolvido")

        leitor = self.repo.leitores[emprestimo.leitor_id]
        atraso = (hoje - emprestimo.prazo).days
        multa = round(self.politicas[leitor.tipo].multa(atraso), 2)

        emprestimo.devolvido_em = hoje
        emprestimo.multa = multa
        self.repo.livros[emprestimo.livro_id].disponivel = True

        if multa > 0:
            corpo = f"Devolução registrada com {atraso} dia(s) de atraso. Multa: R$ {multa:.2f}."
        else:
            corpo = "Devolução registrada. Obrigado por devolver no prazo!"
        self._notificar(leitor, "Devolução registrada", corpo)
        return emprestimo


class ServicoRelatorios:
    def __init__(self, repo: RepositorioMemoria, formatadores: dict[str, Formatador]):
        self.repo = repo
        self.formatadores = formatadores

    def atrasos(self, hoje: date, formato: str) -> tuple[str, str]:
        formatador = self.formatadores.get(formato)
        if formatador is None:
            raise ErroBiblioteca(400, "formato_invalido", "Formato de relatório inválido")
        linhas = [
            {
                "leitor": self.repo.leitores[e.leitor_id].nome,
                "livro": self.repo.livros[e.livro_id].titulo,
                "prazo": e.prazo.isoformat(),
                "dias_atraso": (hoje - e.prazo).days,
            }
            for e in self.repo.atrasados(hoje)
        ]
        return formatador.formatar(linhas), formatador.media_type
