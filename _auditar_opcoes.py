"""Lista questões funcionais com alternativas em falta."""
import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"
OUT = BASE / "_opcoes_incompletas.json"


def campo(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = str(v).strip()
    return "" if t.lower() == "nan" else t


def normalizar(row):
    q = {k: campo(v) for k, v in row.items()}
    for letra in "ABCD":
        q[f"opcao{letra}"] = campo(row.get(f"opcao{letra}"))
    if q.get("resposta_correta"):
        q["resposta_correta"] = q["resposta_correta"].lower()
    return q


def opcoes_preenchidas(q):
    return sum(1 for letra in "ABCD" if campo(q.get(f"opcao{letra}")))


def resposta_valida(q):
    return campo(q.get("resposta_correta")).lower() in "abcd"


def pergunta_funcional(q):
    if not resposta_valida(q):
        return False
    if len(campo(q.get("pergunta")).split()) < 3:
        return False
    letra = campo(q.get("resposta_correta")).upper()
    if not campo(q.get(f"opcao{letra}")):
        return False
    return opcoes_preenchidas(q) >= 2


def deduplicar(records):
    por_id = {}
    for r in records:
        qid = r.get("id")
        if qid is None or (isinstance(qid, float) and pd.isna(qid)):
            continue
        por_id[int(qid)] = r
    unicas = []
    textos = set()
    for r in por_id.values():
        texto = campo(r.get("pergunta")).lower()
        if not texto or texto in textos:
            continue
        textos.add(texto)
        unicas.append(r)
    return unicas


def main():
    df = pd.read_excel(EXCEL)
    records = [normalizar(r) for r in df.to_dict("records")]
    unicas = deduplicar(records)
    funcionais = [q for q in unicas if pergunta_funcional(q)]

    incompletas = []
    for q in funcionais:
        vazias = [letra for letra in "ABCD" if not campo(q.get(f"opcao{letra}"))]
        if not vazias:
            continue
        incompletas.append(
            {
                "id": int(q["id"]),
                "n_opcoes": opcoes_preenchidas(q),
                "vazias": vazias,
                "correta": campo(q.get("resposta_correta")).upper(),
                "pergunta": campo(q.get("pergunta")),
                "opcoes": {letra: campo(q.get(f"opcao{letra}")) for letra in "ABCD"},
                "fonte_imt": campo(q.get("fonte_imt")),
            }
        )

    por_n = {}
    for item in incompletas:
        por_n.setdefault(item["n_opcoes"], []).append(item["id"])

    rel = {
        "total_unicas": len(unicas),
        "total_funcionais": len(funcionais),
        "incompletas": len(incompletas),
        "por_n_opcoes": {str(k): len(v) for k, v in sorted(por_n.items())},
        "ids_por_n_opcoes": {str(k): sorted(v) for k, v in sorted(por_n.items())},
        "detalhe": sorted(incompletas, key=lambda x: (x["n_opcoes"], x["id"])),
    }
    OUT.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Funcionais: {len(funcionais)}")
    print(f"Com alternativas em falta: {len(incompletas)}")
    for n in sorted(por_n):
        print(f"  {n} opções preenchidas: {len(por_n[n])} questões -> IDs {sorted(por_n[n])}")
    print()
    for item in rel["detalhe"]:
        vaz = ",".join(item["vazias"])
        print(f"#{item['id']} ({item['n_opcoes']}/4) vazias={vaz} correta={item['correta']}")
        print(f"  {item['pergunta'][:120]}")
        for letra in "ABCD":
            txt = item["opcoes"][letra]
            if txt:
                mark = "*" if letra == item["correta"] else " "
                print(f"  {mark}{letra}) {txt[:90]}")
        print()


if __name__ == "__main__":
    main()