"""Confere, lendo os arquivos de workflow, quais missões do laboratório já estão no pipeline.

Uso: python scripts/conferir_pipeline.py [PASTA_DO_REPOSITORIO]

O conferidor só lê o YAML. Ele não sabe se o pipeline ficou verde no GitHub:
para isso, abram a aba Actions. E a missão 4 (proteger a main) é uma configuração
do repositório, então não aparece aqui.
"""

import sys
from pathlib import Path

import yaml


def carregar(pasta: Path) -> list[dict]:
    arquivos = sorted((pasta / ".github" / "workflows").glob("*.y*ml"))
    workflows = []
    for arquivo in arquivos:
        try:
            dados = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as erro:
            print(f"✗ {arquivo.name}: YAML inválido ({erro.__class__.__name__})")
            continue
        # O YAML lê a chave `on` como o booleano True.
        dados["on"] = dados.pop(True, dados.get("on", {}))
        dados["_arquivo"] = arquivo.name
        workflows.append(dados)
    return workflows


def gatilhos(wf: dict) -> dict:
    on = wf.get("on") or {}
    if isinstance(on, str):
        return {on: {}}
    if isinstance(on, list):
        return {g: {} for g in on}
    return {g: (v or {}) for g, v in on.items()}


def jobs(workflows: list[dict]):
    for wf in workflows:
        for nome, job in (wf.get("jobs") or {}).items():
            yield wf, nome, job or {}


def passos(job: dict) -> list[dict]:
    return [p for p in job.get("steps") or [] if isinstance(p, dict)]


def texto_dos_passos(job: dict) -> str:
    partes = []
    for p in passos(job):
        partes.append(str(p.get("run", "")))
        partes.append(str(p.get("uses", "")))
        partes.append(str(p.get("with", "")))
    return "\n".join(partes)


def algum_job(workflows, condicao) -> bool:
    return any(condicao(wf, nome, job) for wf, nome, job in jobs(workflows))


def versoes_da_matriz(job: dict) -> list[str]:
    matriz = (job.get("strategy") or {}).get("matrix") or {}
    valores = matriz.get("python-version") or matriz.get("python") or []
    return [str(v) for v in valores] if isinstance(valores, list) else []


def limite_de_cobertura(texto: str) -> float | None:
    tokens = texto.replace("=", " ").split()
    for i, token in enumerate(tokens):
        if token == "--cov-fail-under" and i + 1 < len(tokens):
            try:
                return float(tokens[i + 1])
            except ValueError:
                return None
    return None


def missoes(workflows: list[dict]) -> list[tuple[str, list[tuple[str, bool]]]]:
    tem_push = any("push" in gatilhos(wf) for wf in workflows)
    tem_pr = any("pull_request" in gatilhos(wf) for wf in workflows)
    tem_tag = any(
        "tags" in (gatilhos(wf).get("push") or {}) for wf in workflows if "push" in gatilhos(wf)
    )

    limites = [limite_de_cobertura(texto_dos_passos(j)) for _, _, j in jobs(workflows)]
    limites = [x for x in limites if x is not None]

    def tem(trecho):
        return algum_job(workflows, lambda wf, n, j: trecho in texto_dos_passos(j))

    def matriz_ok(wf, nome, job):
        versoes = versoes_da_matriz(job)
        return len(versoes) >= 2 and "3.11" in versoes

    def imagem_depende_dos_testes(wf, nome, job):
        return "docker build" in texto_dos_passos(job) and bool(job.get("needs"))

    def permissao(job, chave, valor):
        return (job.get("permissions") or {}).get(chave) == valor

    def publica_imagem(wf, nome, job):
        t = texto_dos_passos(job)
        empurra = "docker push" in t or "push: true" in t.lower() or "'push': True" in t
        return "ghcr.io" in t and empurra and permissao(job, "packages", "write")

    def publica_pages(wf, nome, job):
        return "actions/deploy-pages" in texto_dos_passos(job) and permissao(job, "pages", "write")

    def cd_so_no_push(wf, nome, job):
        t = texto_dos_passos(job)
        eh_cd = "deploy-pages" in t or "docker push" in t
        condicao = str(job.get("if", ""))
        return eh_cd and ("push" in condicao or "refs/heads/main" in condicao)

    return [
        (
            "Missão 1 · Primeiro pipeline",
            [
                ("existe um workflow em .github/workflows/", bool(workflows)),
                ("roda em push", tem_push),
                ("roda em pull_request", tem_pr),
                ("algum passo roda pytest", tem("pytest")),
            ],
        ),
        (
            "Missão 3 · Qualidade",
            [
                ("algum passo roda ruff check", tem("ruff check")),
                ("matriz com Python 3.11 e outras versões", algum_job(workflows, matriz_ok)),
                ("cobertura mínima de pelo menos 80%", any(x >= 80 for x in limites)),
            ],
        ),
        (
            "Missão 5 · Imagem Docker",
            [
                (
                    "docker build roda depois dos testes (needs)",
                    algum_job(workflows, imagem_depende_dos_testes),
                ),
                ("teste de fumaça chama /saude", tem("/saude")),
            ],
        ),
        (
            "Missão 6 · Entrega contínua",
            [
                (
                    "publica a imagem no ghcr.io (packages: write)",
                    algum_job(workflows, publica_imagem),
                ),
                ("publica no GitHub Pages (pages: write)", algum_job(workflows, publica_pages)),
                ("jobs de CD só rodam em push, nunca em PR", algum_job(workflows, cd_so_no_push)),
            ],
        ),
        (
            "Desafio · Versões",
            [
                ("pipeline roda quando uma tag v* é enviada", tem_tag),
                ("cria uma release", tem("gh release create") or tem("action-gh-release")),
                ("usa cache do pip", tem("cache")),
            ],
        ),
    ]


def main():
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    workflows = carregar(pasta)
    print(f"Workflows encontrados: {[wf['_arquivo'] for wf in workflows] or 'nenhum'}\n")
    completas = 0
    lista = missoes(workflows)
    for titulo, itens in lista:
        ok = all(passou for _, passou in itens)
        completas += ok
        print(f"{'✔' if ok else '·'} {titulo}")
        for descricao, passou in itens:
            print(f"    {'✔' if passou else '✗'} {descricao}")
    print("\n  Missão 2 (quebrar de propósito) e Missão 4 (proteger a main) não aparecem no YAML:")
    print("  confiram na aba Actions e em Settings › Rules.")
    print(f"\nMissões completas no YAML: {completas} de {len(lista)}")


if __name__ == "__main__":
    main()
