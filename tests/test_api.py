"""Testes de integração: a API vista de fora, pelas rotas HTTP."""

from datetime import date

import pytest

SEXTA = date(2026, 10, 16)  # prazo cai sexta 30/10
SABADO = date(2026, 10, 17)  # prazo cairia sábado 31/10 -> segunda 02/11
DOMINGO = date(2026, 10, 18)  # prazo cairia domingo 01/11 -> segunda 02/11


# ------------------------------ empréstimo ------------------------------


def test_emprestimo_criado_com_prazo_de_14_dias(cliente, mudar_data, emprestar):
    mudar_data(SEXTA)
    r = emprestar(1, 1)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["data_emprestimo"] == "2026-10-16"
    assert corpo["prazo"] == "2026-10-30"
    assert corpo["devolvido_em"] is None
    assert corpo["multa"] is None


@pytest.mark.parametrize("dia", [SABADO, DOMINGO])
def test_prazo_no_fim_de_semana_vai_para_segunda(mudar_data, emprestar, dia):
    mudar_data(dia)
    assert emprestar(1, 1).json()["prazo"] == "2026-11-02"


def test_livro_fica_indisponivel(cliente, emprestar):
    emprestar(1, 3)
    livros = {livro["id"]: livro for livro in cliente.get("/livros").json()}
    assert livros[3]["disponivel"] is False
    assert livros[1]["disponivel"] is True


@pytest.mark.parametrize(
    "leitor, livro, status, erro",
    [
        (999, 1, 404, "leitor_nao_encontrado"),
        (1, 999, 404, "livro_nao_encontrado"),
    ],
)
def test_emprestimo_com_ids_inexistentes(emprestar, leitor, livro, status, erro):
    r = emprestar(leitor, livro)
    assert r.status_code == status
    assert r.json()["detail"]["erro"] == erro


def test_livro_emprestado_nao_pode_ser_emprestado_de_novo(emprestar):
    emprestar(1, 1)
    r = emprestar(2, 1)
    assert r.status_code == 409
    assert r.json()["detail"]["erro"] == "livro_indisponivel"


@pytest.mark.parametrize("leitor", [1, 2])
def test_limite_de_3_emprestimos(emprestar, leitor):
    for livro in (1, 2, 3):
        assert emprestar(leitor, livro).status_code == 201
    r = emprestar(leitor, 4)
    assert r.status_code == 409
    assert r.json()["detail"]["erro"] == "limite_excedido"


def test_devolver_libera_vaga_no_limite(emprestar, devolver):
    ids = [emprestar(1, livro).json()["id"] for livro in (1, 2, 3)]
    devolver(ids[0])
    assert emprestar(1, 4).status_code == 201


def test_corpo_invalido_retorna_422(cliente):
    assert cliente.post("/emprestimos", json={"leitor_id": 1}).status_code == 422


# ------------------------------ devolução e multa ------------------------------


@pytest.mark.parametrize(
    "leitor, devolucao, multa",
    [
        (1, date(2026, 10, 29), 0.0),  # antes do prazo
        (1, date(2026, 10, 30), 0.0),  # no dia do prazo
        (1, date(2026, 11, 3), 8.0),  # 4 dias x R$ 2
        (1, date(2026, 12, 30), 50.0),  # teto
        (2, date(2026, 11, 3), 4.0),  # estudante: metade
        (2, date(2026, 12, 30), 25.0),  # estudante: metade do teto
    ],
)
def test_multa(mudar_data, emprestar, devolver, leitor, devolucao, multa):
    mudar_data(SEXTA)
    emprestimo_id = emprestar(leitor, 1).json()["id"]
    mudar_data(devolucao)
    r = devolver(emprestimo_id)
    assert r.status_code == 200
    assert r.json()["multa"] == multa
    assert r.json()["devolvido_em"] == devolucao.isoformat()


def test_devolucao_libera_o_livro(cliente, emprestar, devolver):
    emprestimo_id = emprestar(1, 1).json()["id"]
    devolver(emprestimo_id)
    assert cliente.get("/livros").json()[0]["disponivel"] is True


def test_devolver_inexistente_retorna_404(devolver):
    r = devolver(999)
    assert r.status_code == 404
    assert r.json()["detail"]["erro"] == "emprestimo_nao_encontrado"


def test_devolver_duas_vezes_retorna_409(emprestar, devolver):
    emprestimo_id = emprestar(1, 1).json()["id"]
    devolver(emprestimo_id)
    r = devolver(emprestimo_id)
    assert r.status_code == 409
    assert r.json()["detail"]["erro"] == "ja_devolvido"


# ------------------------------ leitores ------------------------------


def test_cadastrar_leitor(cliente, emprestar):
    dados = {"nome": "Davi", "tipo": "comum", "email": "davi@exemplo.com"}
    r = cliente.post("/leitores", json=dados)
    assert r.status_code == 201
    assert r.json()["id"] == 3
    assert emprestar(3, 1).status_code == 201


@pytest.mark.parametrize(
    "dados, erro",
    [
        ({"nome": "X", "tipo": "vip", "email": "x@exemplo.com"}, "tipo_invalido"),
        ({"nome": "X", "tipo": "comum", "email": "sem-arroba"}, "email_invalido"),
    ],
)
def test_cadastro_invalido(cliente, dados, erro):
    r = cliente.post("/leitores", json=dados)
    assert r.status_code == 422
    assert r.json()["detail"]["erro"] == erro


# ------------------------------ notificações ------------------------------


def test_emprestimo_envia_email(cliente, mudar_data, emprestar):
    mudar_data(SEXTA)
    emprestar(1, 1)
    notificacoes = cliente.get("/notificacoes").json()
    assert len(notificacoes) == 1
    n = notificacoes[0]
    assert n["canal"] == "email"
    assert n["para"] == "ana@exemplo.com"
    assert n["assunto"] == "Empréstimo confirmado"
    assert "Dom Casmurro" in n["corpo"]
    assert "30/10/2026" in n["corpo"]


def test_devolucao_atrasada_envia_email_com_multa(cliente, mudar_data, emprestar, devolver):
    mudar_data(SEXTA)
    emprestimo_id = emprestar(1, 1).json()["id"]
    mudar_data(date(2026, 11, 3))
    devolver(emprestimo_id)
    ultima = cliente.get("/notificacoes").json()[-1]
    assert ultima["assunto"] == "Devolução registrada"
    assert "R$ 8.00" in ultima["corpo"]


def test_devolucao_no_prazo_agradece(cliente, emprestar, devolver):
    emprestimo_id = emprestar(1, 1).json()["id"]
    devolver(emprestimo_id)
    assert "Obrigado" in cliente.get("/notificacoes").json()[-1]["corpo"]


def test_estado_reinicia_entre_testes(cliente):
    assert cliente.get("/notificacoes").json() == []


# ------------------------------ relatório ------------------------------


def _cenario_com_atraso(mudar_data, emprestar):
    mudar_data(SEXTA)
    emprestar(1, 1)  # prazo 30/10
    emprestar(2, 2)  # prazo 30/10
    mudar_data(date(2026, 11, 2))  # 3 dias depois


def test_relatorio_json(cliente, mudar_data, emprestar):
    _cenario_com_atraso(mudar_data, emprestar)
    r = cliente.get("/relatorios/atrasos?formato=json")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == [
        {"leitor": "Ana", "livro": "Dom Casmurro", "prazo": "2026-10-30", "dias_atraso": 3},
        {"leitor": "Bruno", "livro": "O Cortiço", "prazo": "2026-10-30", "dias_atraso": 3},
    ]


def test_relatorio_csv(cliente, mudar_data, emprestar):
    _cenario_com_atraso(mudar_data, emprestar)
    r = cliente.get("/relatorios/atrasos?formato=csv")
    assert r.headers["content-type"].startswith("text/csv")
    assert r.text.splitlines() == [
        "leitor;livro;prazo;dias_atraso",
        "Ana;Dom Casmurro;2026-10-30;3",
        "Bruno;O Cortiço;2026-10-30;3",
    ]


def test_relatorio_ignora_devolvidos_e_em_dia(cliente, mudar_data, emprestar, devolver):
    mudar_data(SEXTA)
    emprestimo_id = emprestar(1, 1).json()["id"]
    devolver(emprestimo_id)
    mudar_data(date(2026, 10, 20))
    emprestar(2, 2)
    mudar_data(date(2026, 11, 2))
    assert cliente.get("/relatorios/atrasos").json() == []


def test_relatorio_formato_invalido(cliente):
    r = cliente.get("/relatorios/atrasos?formato=xml")
    assert r.status_code == 400
    assert r.json()["detail"]["erro"] == "formato_invalido"


def test_saude(cliente):
    assert cliente.get("/saude").json() == {"status": "ok"}
