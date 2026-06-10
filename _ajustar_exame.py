import pandas as pd
import re
from pathlib import Path

EXCEL = Path(__file__).parent / "questoes sem rep.xlsx"

PASSAGEIROS_KW = (
    "passageiros", "autocarro", "autocarros", "carreira", "carreiras",
    "autocarro", "serviço regular", "servico regular", "expresso",
)
MERCADORIAS_KW = (
    "mercadorias", "mercadoria", "carga", "adr", "guia de transporte",
    "alvará", "alvara", "conta de outrem",
)


def classificar_tema(row):
    texto = " ".join(
        str(row.get(c, "")) for c in ("pergunta", "explicacao", "opcaoA", "opcaoB", "opcaoC", "opcaoD")
    ).lower()
    p = any(k in texto for k in PASSAGEIROS_KW)
    m = any(k in texto for k in MERCADORIAS_KW)
    if p and m:
        return "misto"
    if p:
        return "passageiros"
    if m:
        return "mercadorias"
    return "comum"


def main():
    df = pd.read_excel(EXCEL)

    # Remover avisos de "fora de escopo" — passageiros faz parte do exame CAM
    if "notas_revisao" in df.columns:
        df["notas_revisao"] = df["notas_revisao"].fillna("").astype(str)
        df["notas_revisao"] = df["notas_revisao"].str.replace(
            r"Questão de transporte de passageiros — verificar relevância para exame CAM mercadorias\.\s*",
            "",
            regex=True,
        ).str.strip()

    if "status_revisao" in df.columns:
        df["status_revisao"] = df["status_revisao"].fillna("").astype(str)
        df["status_revisao"] = df["status_revisao"].str.replace("; revisar_escopo", "", regex=False)
        df["status_revisao"] = df["status_revisao"].str.replace("revisar_escopo", "", regex=False)
        df["status_revisao"] = df["status_revisao"].str.strip("; ").str.strip()

    df["tema_exame"] = df.apply(classificar_tema, axis=1)

    # Melhorar explicações de questões corrigidas (foco exame IMT)
    fixes_exp = {
        2: "Resposta aceite no exame (DL 257/2007 / IMT): 9.000 € no 1.º veículo; 5.000 € (pesado) ou 900 € (ligeiro) por veículo adicional.",
        187: "Resposta aceite no exame: todas as afirmações sobre o airbag são verdadeiras.",
    }
    for qid, exp in fixes_exp.items():
        mask = df["id"] == qid
        if mask.any():
            df.loc[mask, "explicacao"] = exp

    # Q229 — manter resposta B (padrão habitual em testes de passageiros)
    mask229 = df["id"] == 229
    if mask229.any():
        df.loc[mask229, "explicacao"] = (
            "Resposta habitualmente aceite nos testes de passageiros do exame CAM/CP. "
            "Confirme sempre com o manual da sua entidade formadora."
        )

    df.to_excel(EXCEL, index=False)

    print(f"Total questões: {len(df)}")
    print(df["tema_exame"].value_counts().to_string())
    print(f"Passageiros (incl. misto): {df['tema_exame'].isin(['passageiros','misto']).sum()}")


if __name__ == "__main__":
    main()