"""Gera a página pública da API: documentação (OpenAPI + Redoc) e link da cobertura.

Uso: python scripts/gerar_docs.py PASTA_DE_SAIDA
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from biblioteca.main import app  # noqa: E402

PAGINA = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API da Biblioteca</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; }}
    header {{ background: #0B2E8A; color: #F4F7FB; padding: 16px 24px; }}
    header a {{ color: #4FD1C5; margin-right: 16px; }}
    header small {{ display: block; opacity: .8; margin-top: 4px; }}
  </style>
</head>
<body>
  <header>
    <strong>API da Biblioteca</strong>
    <small>Publicado pelo pipeline · commit {commit} · {quando}</small>
    <p><a href="cobertura/index.html">Relatório de cobertura</a>
       <a href="openapi.json">openapi.json</a></p>
  </header>
  <redoc spec-url="openapi.json"></redoc>
  <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


def main(saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "openapi.json").write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    commit = os.environ.get("GITHUB_SHA", "local")[:7]
    quando = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    (saida / "index.html").write_text(PAGINA.format(commit=commit, quando=quando), encoding="utf-8")
    print(f"Página gerada em {saida}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "site"))
