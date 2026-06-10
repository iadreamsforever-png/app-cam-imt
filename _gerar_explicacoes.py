"""Gera explicações úteis quando o Excel só tem o prefixo IMT."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from _alinhar_imt import s

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"
OUT = BASE / "_gerar_explicacoes.json"

PREFIXO = re.compile(r"^Resposta aceite no exame IMT[.:]?\s*", re.I)


def explicacao_de_opcao(letra: str, opcao: str, pergunta: str) -> str:
    tema = s(pergunta)
    if tema.endswith(":"):
        tema = tema[:-1]
    if len(tema) > 120:
        tema = tema[:117] + "..."
    return (
        f"A resposta correta é a opção {letra}) {opcao}. "
        f"No exame CAM do IMT, esta alternativa responde corretamente à questão "
        f"«{tema}»."
    )


def normalizar_explicacao(row) -> tuple[str, str]:
    exp = s(row.get("explicacao"))
    letra = s(row.get("resposta_correta")).upper()
    opcao = s(row.get(f"opcao{letra}"))

    if not exp:
        if opcao:
            return explicacao_de_opcao(letra, opcao, s(row.get("pergunta"))), "gerada"
        return exp, "vazia"

    if PREFIXO.match(exp):
        resto = PREFIXO.sub("", exp).strip()
        if len(resto) >= 25:
            return resto, "prefixo_removido"
        if opcao:
            return explicacao_de_opcao(letra, opcao, s(row.get("pergunta"))), "gerada"
        return resto or exp, "sem_opcao"

    if exp.lower().startswith("resposta aceite no exame imt"):
        resto = PREFIXO.sub("", exp).strip()
        if len(resto) >= 25:
            return resto, "prefixo_removido"

    return exp, "mantida"


def main():
    df = pd.read_excel(EXCEL)
    stats = {"gerada": 0, "prefixo_removido": 0, "mantida": 0, "vazia": 0, "sem_opcao": 0}

    for idx, row in df.iterrows():
        nova, modo = normalizar_explicacao(row)
        stats[modo] = stats.get(modo, 0) + 1
        if s(row.get("explicacao")) != nova:
            df.at[idx, "explicacao"] = nova

    df.to_excel(EXCEL, index=False)
    rel = {"total": len(df), **stats}
    OUT.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rel, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()