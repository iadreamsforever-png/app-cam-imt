import json
import math
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"


def s(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v).strip()


CORRECOES = {
    2: {
        "opcaoD": "Não pode ser inferior a € 9 000 pelo primeiro veículo automóvel licenciado ou € 5 000 ou € 900 por cada veículo adicional, consoante se trate de veículo pesado ou ligeiro",
        "explicacao": "Capacidade financeira (IMT/DL 257/2007): 9.000 € no 1.º veículo; 5.000 € (pesado) ou 900 € (ligeiro) por cada veículo adicional.",
        "notas_revisao": "Corrigido valor do veículo ligeiro: 1.500 € → 900 € (fonte: imt-ip.pt).",
    },
    170: {
        "opcaoD": "Sociedades comerciais, cooperativas, empresas públicas e outras entidades que reúnam os requisitos de acesso",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    186: {
        "opcaoD": "Falsa — não existe sanção para a contratação de imigrantes em situação irregular",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    187: {
        "opcaoD": "Apenas a primeira afirmação é verdadeira",
        "resposta_correta": "c",
        "explicacao": "O airbag é complementar ao cinto de segurança; usado isoladamente pode causar lesões. Todas as afirmações são verdadeiras.",
        "notas_revisao": "Resposta corrigida D→C; opção D preenchida.",
    },
    188: {
        "opcaoC": "Consumir exclusivamente alimentos ricos em gordura animal",
        "notas_revisao": "Preenchida opção C em falta.",
    },
    194: {
        "opcaoD": "Deve evitar cobrir os feridos para não provocar choque térmico",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    199: {
        "opcaoD": "Ligado e frio, para o óleo estar mais viscoso",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    203: {
        "opcaoD": "Na amarração directa entre a carga e o chão do veículo, sem ligação lateral",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    204: {
        "opcaoD": "Circular sem paragens para chegar mais depressa ao destino",
        "notas_revisao": "Preenchida opção D em falta.",
    },
    207: {
        "opcaoA": "2 metros a contar do solo",
        "resposta_correta": "c",
        "explicacao": "A altura máxima da carga é de 4 metros a contar do solo (regra geral em Portugal).",
        "notas_revisao": "Resposta corrigida B→C (4 m); opção A preenchida.",
    },
}

def main():
    df = pd.read_excel(EXCEL)
    df["status_revisao"] = ""
    df["notas_revisao"] = ""

    for qid, fixes in CORRECOES.items():
        mask = df["id"] == qid
        if not mask.any():
            print(f"AVISO: ID {qid} não encontrado")
            continue
        for col, val in fixes.items():
            df.loc[mask, col] = val
        df.loc[mask, "status_revisao"] = "corrigida"

    # remover duplicadas (manter primeira ocorrência)
    antes = len(df)
    df["_key"] = df["pergunta"].str.strip().str.lower()
    dup_mask = df.duplicated(subset="_key", keep="first")
    removidas = df[dup_mask][["id", "pergunta"]].copy()
    df = df[~dup_mask].drop(columns="_key").reset_index(drop=True)
    depois = len(df)

    # backup
    backup = BASE / "questoes_backup_antes_revisao.xlsx"
    pd.read_excel(EXCEL).to_excel(backup, index=False)

    df.to_excel(EXCEL, index=False)
    removidas.to_excel(BASE / "questoes_duplicadas_removidas.xlsx", index=False)

    resumo = {
        "total_antes": antes,
        "total_depois": depois,
        "duplicadas_removidas": int(dup_mask.sum()),
        "correcoes_aplicadas": len(CORRECOES),
        "passageiros_no_banco": int(
            df["pergunta"].str.contains("passageiro|autocarro|carreira", case=False, na=False).sum()
        ),
    }
    (BASE / "_resumo_revisao.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()