import json
import math
import re
from pathlib import Path

def s(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v)

data = json.loads(Path("_questoes_full.json").read_text(encoding="utf-8"))
issues = []

for q in data:
    qid = q["id"]
    resp = s(q["resposta_correta"]).lower()
    opts = {L: s(q[f"opcao{L}"]) for L in "ABCD"}
    exp = s(q["explicacao"])

    # empty options
    for L in "ABCD":
        if not opts[L]:
            issues.append({"id": qid, "tipo": "opcao_vazia", "detalhe": f"Opção {L} vazia", "gravidade": "alta"})

    # empty correct answer option
    if resp and not opts.get(resp.upper(), opts.get(resp, "")):
        issues.append({"id": qid, "tipo": "resposta_vazia", "detalhe": f"Resposta marcada {resp.upper()} está vazia", "gravidade": "critica"})

    # known legal errors
    if qid == 2 and "1500" in opts["D"]:
        issues.append({"id": qid, "tipo": "valor_desatualizado", "detalhe": "Capital veículo ligeiro deve ser 900€, não 1500€", "gravidade": "alta"})

    if qid == 207:
        if resp == "b" and "4 metro" in exp.lower():
            issues.append({"id": qid, "tipo": "resposta_incorreta", "detalhe": "Explicação indica 4m mas resposta marcada é B (5m). Correta: C", "gravidade": "critica"})

    if qid == 187:
        if resp == "d" and not opts["D"] and "todas" in opts["C"].lower():
            issues.append({"id": qid, "tipo": "resposta_incorreta", "detalhe": "Opção C diz que todas são verdadeiras. Resposta deve ser C, não D", "gravidade": "critica"})

    # exp mentions value in wrong option
    if "4 metro" in exp.lower() and resp == "b" and "4 metro" in opts["C"].lower():
        issues.append({"id": qid, "tipo": "incoerencia", "detalhe": "Explicação refere 4 metros alinhado com opção C", "gravidade": "critica"})

# duplicates
seen = {}
for q in data:
    t = s(q["pergunta"]).strip().lower()
    seen.setdefault(t, []).append(q["id"])
for t, ids in seen.items():
    if len(ids) > 1 and t:
        issues.append({"id": ids[0], "tipo": "duplicada", "detalhe": f"Texto repetido nos IDs {ids}", "gravidade": "media"})

out = Path("_issues.json")
out.write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")

from collections import Counter
c = Counter(i["tipo"] for i in issues)
print(f"Total issues: {len(issues)}")
for k, v in c.most_common():
    print(f"  {k}: {v}")

crit = [i for i in issues if i["gravidade"] in ("critica", "alta")]
print(f"\nCriticas/altas: {len(crit)}")
for i in crit:
    print(f"  ID {i['id']}: [{i['tipo']}] {i['detalhe']}")