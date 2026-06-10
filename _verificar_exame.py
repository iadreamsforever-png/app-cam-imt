import math
import pandas as pd
from pathlib import Path

EXCEL = Path(__file__).parent / "questoes sem rep.xlsx"


def s(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v).strip()


def main():
    df = pd.read_excel(EXCEL)
    print(f"Total: {len(df)}")
    print(f"Colunas: {list(df.columns)}")

    if "status_revisao" in df.columns:
        escopo = df["status_revisao"].fillna("").str.contains("escopo", case=False)
        print(f"Avisos escopo: {escopo.sum()}")

    if "notas_revisao" in df.columns:
        bad = df["notas_revisao"].fillna("").str.contains(
            r"mercadorias\.\s*$|fora de escopo|verificar relev", case=False, regex=True
        )
        print(f"Notas escopo antigas: {bad.sum()}")

    for col in ["opcaoA", "opcaoB", "opcaoC", "opcaoD"]:
        empty = df[col].isna() | (df[col].astype(str).str.strip() == "")
        if empty.any():
            print(f"{col} vazias ({empty.sum()}): {df.loc[empty, 'id'].tolist()}")

    resp = df["resposta_correta"].fillna("").astype(str).str.strip().str.lower()
    invalid = ~resp.isin(["a", "b", "c", "d"])
    if invalid.any():
        print(f"Respostas inválidas: {df.loc[invalid, ['id', 'resposta_correta']].to_string()}")

    if "tema_exame" in df.columns:
        print("\ntema_exame:")
        print(df["tema_exame"].value_counts().to_string())

    for qid in [2, 35, 187, 207, 229]:
        r = df[df["id"] == qid]
        if r.empty:
            print(f"\nID {qid}: AUSENTE")
            continue
        r = r.iloc[0]
        print(f"\nID {qid} | resp={r['resposta_correta']} | tema={r.get('tema_exame', '?')}")
        print(f"  Exp: {s(r.get('explicacao'))[:120]}")


if __name__ == "__main__":
    main()