"""Verificação final antes do deploy Streamlit."""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"
APP = BASE / "app_cam.py"


def campo(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = str(v).strip()
    return "" if t.lower() == "nan" else t


def pergunta_funcional(q) -> bool:
    rc = campo(q.get("resposta_correta")).lower()
    if rc not in "abcd":
        return False
    if len(campo(q.get("pergunta")).split()) < 3:
        return False
    if not campo(q.get(f"opcao{rc.upper()}")):
        return False
    return sum(1 for L in "ABCD" if campo(q.get(f"opcao{L}"))) >= 2


def dedup(records):
    por_id = {}
    for r in records:
        qid = r.get("id")
        if qid is None or (isinstance(qid, float) and pd.isna(qid)):
            continue
        por_id[int(qid)] = r
    unicas, textos = [], set()
    for r in por_id.values():
        t = campo(r.get("pergunta")).lower()
        if not t or t in textos:
            continue
        textos.add(t)
        unicas.append(r)
    return unicas


def main():
    erros = []
    avisos = []

    if not APP.exists():
        erros.append("app_cam.py em falta")
    else:
        ast.parse(APP.read_text(encoding="utf-8"))
        texto = APP.read_text(encoding="utf-8")
        if "_explicacoes_ricas" in texto or "_alinhar_imt" in texto:
            erros.append("app_cam.py importa módulos auxiliares não seguros para deploy")

    req = BASE / "requirements.txt"
    if not req.exists():
        erros.append("requirements.txt em falta")
    else:
        for pkg in ("streamlit", "pandas", "openpyxl"):
            if pkg not in req.read_text(encoding="utf-8").lower():
                erros.append(f"requirements.txt sem {pkg}")

    if not EXCEL.exists():
        erros.append("questoes sem rep.xlsx em falta")
    else:
        df = pd.read_excel(EXCEL)
        records = [dict(r) for r in df.to_dict("records")]
        unicas = dedup(records)
        func = [q for q in unicas if pergunta_funcional(q)]
        incompletas = []
        for q in func:
            vazias = [L for L in "ABCD" if not campo(q.get(f"opcao{L}"))]
            if vazias:
                incompletas.append((q["id"], vazias))

        sem_exp = [q["id"] for q in func if not campo(q.get("explicacao"))]
        genericas = [
            q["id"]
            for q in func
            if "esta alternativa responde corretamente" in campo(q.get("explicacao")).lower()
            or "por exemplo," in campo(q.get("explicacao")).lower()
        ]

        if len(func) < 60:
            erros.append(f"menos de 60 questões funcionais ({len(func)})")
        if incompletas:
            avisos.append(f"{len(incompletas)} funcionais com opções vazias (ex: {incompletas[:3]})")
        if sem_exp:
            erros.append(f"{len(sem_exp)} questões sem explicação")
        if genericas:
            erros.append(f"{len(genericas)} explicações genéricas restantes")

    rel = {
        "ok": len(erros) == 0,
        "erros": erros,
        "avisos": avisos,
        "funcionais": len(func) if EXCEL.exists() else 0,
        "excel_linhas": len(df) if EXCEL.exists() else 0,
    }
    (BASE / "_verificar_deploy.json").write_text(
        json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(rel, ensure_ascii=False, indent=2))
    sys.exit(0 if rel["ok"] else 1)


if __name__ == "__main__":
    main()