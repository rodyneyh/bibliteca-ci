"""API da Biblioteca. Rode com: fastapi dev biblioteca/main.py

Este arquivo só traduz HTTP e monta as peças (composição).
Contrato usado pelos testes: `app`, `hoje` e `reiniciar()`.
"""

from dataclasses import asdict
from datetime import date

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from biblioteca.erros import ErroBiblioteca
from biblioteca.modelos import Emprestimo
from biblioteca.notificacao import CaixaDeSaida, NotificadorEmail
from biblioteca.politicas import POLITICAS
from biblioteca.relatorios import FORMATADORES
from biblioteca.repositorio import RepositorioMemoria
from biblioteca.servico import ServicoEmprestimos, ServicoLeitores, ServicoRelatorios

# ---------------- composição: o único lugar que conhece as classes concretas ----------------
repo = RepositorioMemoria()
caixa = CaixaDeSaida()

NOTIFICADORES = [NotificadorEmail(caixa)]

leitores = ServicoLeitores(repo, POLITICAS)
emprestimos = ServicoEmprestimos(repo, POLITICAS, NOTIFICADORES)
relatorios = ServicoRelatorios(repo, FORMATADORES)

app = FastAPI(title="API da Biblioteca")


def hoje() -> date:
    return date.today()


def reiniciar():
    repo.reiniciar()
    caixa.mensagens.clear()


@app.exception_handler(ErroBiblioteca)
def tratar_erro(_: Request, e: ErroBiblioteca):
    corpo = {"detail": {"erro": e.codigo, "mensagem": e.mensagem}}
    return JSONResponse(status_code=e.status, content=corpo)


# ---------------- HTTP ----------------
class LeitorIn(BaseModel):
    nome: str
    tipo: str
    email: str
    telefone: str | None = None


class EmprestimoIn(BaseModel):
    leitor_id: int
    livro_id: int


def emprestimo_json(e: Emprestimo) -> dict:
    return {
        "id": e.id,
        "leitor_id": e.leitor_id,
        "livro_id": e.livro_id,
        "data_emprestimo": e.data_emprestimo.isoformat(),
        "prazo": e.prazo.isoformat(),
        "devolvido_em": e.devolvido_em.isoformat() if e.devolvido_em else None,
        "multa": e.multa,
    }


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.post("/leitores", status_code=201)
def cadastrar_leitor(dados: LeitorIn):
    return asdict(leitores.cadastrar(dados.nome, dados.tipo, dados.email, dados.telefone))


@app.get("/livros")
def listar_livros():
    return [asdict(livro) for livro in repo.livros.values()]


@app.post("/emprestimos", status_code=201)
def criar_emprestimo(dados: EmprestimoIn, data: date = Depends(hoje)):
    return emprestimo_json(emprestimos.emprestar(dados.leitor_id, dados.livro_id, data))


@app.post("/emprestimos/{emprestimo_id}/devolucao")
def devolver(emprestimo_id: int, data: date = Depends(hoje)):
    return emprestimo_json(emprestimos.devolver(emprestimo_id, data))


@app.get("/relatorios/atrasos")
def relatorio_atrasos(formato: str = "json", data: date = Depends(hoje)):
    conteudo, tipo = relatorios.atrasos(data, formato)
    return Response(content=conteudo, media_type=tipo)


@app.get("/notificacoes")
def listar_notificacoes():
    return caixa.mensagens
