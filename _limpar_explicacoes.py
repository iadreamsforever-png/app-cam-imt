"""Remove frases genéricas de contraste das explicações."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from _alinhar_imt import s

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"

REMOVER = [
    re.compile(r"\s*Por exemplo,.*$", re.I | re.S),
    re.compile(
        r"\s*As alternativas .* são afirmações corretas ou recomendadas\.?",
        re.I | re.S,
    ),
    re.compile(r"\s*A opção [A-D]\).*não corresponde ao pedido do enunciado\.?", re.I | re.S),
]


def limpar_texto(texto: str) -> str:
    t = s(texto)
    for pat in REMOVER:
        t = pat.sub("", t).strip()
    return t.rstrip(" .") + "." if t and not t.endswith((".", "!", "?")) else t


def main():
    df = pd.read_excel(EXCEL)
    alteradas = 0
    for idx, row in df.iterrows():
        antiga = s(row.get("explicacao"))
        nova = limpar_texto(antiga)
        if nova != antiga:
            df.at[idx, "explicacao"] = nova
            alteradas += 1
    df.to_excel(EXCEL, index=False)
    restantes = sum(
        1
        for _, r in df.iterrows()
        if "por exemplo," in s(r.explicacao).lower()
    )
    rel = {"alteradas": alteradas, "restantes_por_exemplo": restantes, "total": len(df)}
    (BASE / "_limpar_explicacoes.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(rel, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()