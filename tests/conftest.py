"""Fixtures da rede de segurança. Só dependem do contrato de biblioteca.main:
`app`, `hoje` e `reiniciar()`. Refatorem à vontade por dentro."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from biblioteca.main import app, hoje, reiniciar


@pytest.fixture(autouse=True)
def estado_limpo():
    reiniciar()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def cliente():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mudar_data():
    def _mudar(nova: date):
        app.dependency_overrides[hoje] = lambda: nova

    return _mudar


@pytest.fixture
def emprestar(cliente):
    def _emprestar(leitor_id, livro_id):
        return cliente.post("/emprestimos", json={"leitor_id": leitor_id, "livro_id": livro_id})

    return _emprestar


@pytest.fixture
def devolver(cliente):
    def _devolver(emprestimo_id):
        return cliente.post(f"/emprestimos/{emprestimo_id}/devolucao")

    return _devolver
