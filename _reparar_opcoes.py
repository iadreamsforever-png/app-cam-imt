"""Repara questões funcionais com alternativas ou enunciados incompletos."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from _alinhar_imt import match_question, norm, parse_imt_questions, s
from _reparar_e_completar import melhor_bloco_imt

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"
IMT_TEXT = BASE / "_imt_cam_completo.txt"
OUT = BASE / "_reparar_opcoes.json"

# IDs com alternativas em falta (auditoria anterior)
IDS_ALVO = {
    250, 260, 262, 269, 282, 306, 310, 393, 456, 457, 472, 502, 639, 673, 781, 858, 885, 905, 944, 947
}

# Enunciado IMT exato quando o match automático falha
CORRECOES_MANUAIS = {
    250: {
        "opcaoB": "Transmite-se desde que o Instituto da Mobilidade e dos Transportes dê o seu acordo",
    },
    262: {
        "pergunta": (
            "Para realizar uma largada de pombos correio em Bragança, foi cedido a título gratuito, "
            "à Associação Columbófila do Porto, um veículo de 6 ton, afeto ao transporte por conta própria. "
            "Para a Associação poder efetuar este transporte:"
        ),
        "opcaoA": (
            "Torna-se necessária uma autorização a emitir pelo Instituto da Mobilidade e dos Transporte "
            "e o licenciamento do veículo"
        ),
        "opcaoB": "Carece de autorização a emitir pelo Instituto da Mobilidade e dos Transportes",
    },
    269: {
        "opcaoB": (
            "Sociedades comerciais e cooperativas licenciadas pelo Instituto da Mobilidade e dos Transportes"
        ),
    },
    282: {
        "opcaoC": "O Instituto da Mobilidade e dos Transportes",
    },
    947: {
        "pergunta": (
            "O limitador de velocidade permite manter uma velocidade constante sem que seja necessário "
            "pressionar o acelerador do veículo. Esta afirmação é:"
        ),
        "opcaoA": (
            "Falsa, uma vez que o dispositivo que permite manter a velocidade constante é o regulador de velocidade"
        ),
        "opcaoB": (
            "Falsa, uma vez que o dispositivo que permite manter a velocidade constante é o GPS"
        ),
        "opcaoC": (
            "Falsa, uma vez que o dispositivo que permite manter a velocidade constante é o regulador activo de velocidade"
        ),
        "opcaoD": "Verdadeira",
        "resposta_correta": "c",
    },
}

ENUNCIADOS_IMT = {
    393: "O binário do motor é:",
    456: "Assinale a afirmação verdadeira:",
    502: "A tarefa da condução impõe:",
    639: "Antes de iniciar o transporte, entende -se como uma boa prática, com vista a evitar situações de criminalidade e vandalismo:",
    673: "Diga o que fazer em caso de emergência de roubo ou assalto:",
    781: "De acordo com o Observatório de Segurança Rodoviária o nosso país tem vindo a diminuir o número de mortos e feridos graves envolvidos em acidentes de trânsito",
    858: "Perante uma reclamação do cliente devo:",
    885: 'Uma reclamação pode ser vista como uma oportunidade". Uma das frases seguintes é falsa. Indique qual:',
    905: "A bilhética sem contacto (indique a afirmação verdadeira):",
    944: "Relativamente ao tacógrafo digital, indique qual é a afirmação verdadeira:",
    260: "São considerados como  efetuados por entidade diversa do titular do alvará, os transportes em que se verifique alguma das seguintes situações:",
    306: "No planeamento do enchimento da caixa de carga do veículo é imperativo considerar-se:",
    310: "Para garantia, quer da própria segurança, quer da segurança dos outros utentes, o condutor de um veículo de mercadorias deve:",
}


def bloco_por_enunciado(enunciado: str, blocks: list[dict]) -> tuple[dict | None, float]:
    blk, sim = melhor_bloco_imt(enunciado, blocks)
    if blk and sim >= 0.5:
        return blk, sim
    nk = norm(enunciado)
    for b in blocks:
        if norm(b["pergunta"]) == nk:
            return b, 1.0
    for b in blocks:
        kb = norm(b["pergunta"])
        if nk in kb or kb in nk:
            return b, 0.9
    return None, 0.0


def opcoes_preenchidas(row) -> int:
    return sum(1 for letra in "ABCD" if s(row.get(f"opcao{letra}")))


def aplicar_bloco(df: pd.DataFrame, idx: int, blk: dict, manter_gabarito: bool = True) -> list[str]:
    alteracoes = []
    antiga = s(df.at[idx, "pergunta"])
    nova = blk["pergunta"]
    if antiga != nova:
        df.at[idx, "pergunta"] = nova
        alteracoes.append("pergunta")

    gabarito = s(df.at[idx, "resposta_correta"]).lower()
    for letra in "ABCD":
        imt_txt = blk["opts"].get(letra, "")
        if not imt_txt:
            continue
        col = f"opcao{letra}"
        if not s(df.at[idx, col]) or len(imt_txt) > len(s(df.at[idx, col])):
            df.at[idx, col] = imt_txt
            alteracoes.append(col)

    if manter_gabarito and gabarito in "abcd" and s(df.at[idx, f"opcao{gabarito.upper()}"]):
        df.at[idx, "resposta_correta"] = gabarito
    df.at[idx, "fonte_imt"] = "imt_oficial"
    return alteracoes


def main():
    blocks = parse_imt_questions(IMT_TEXT.read_text(encoding="utf-8"))
    df = pd.read_excel(EXCEL)
    relatorio = {"removidos": [], "reparados": [], "sem_alteracao": []}

    # #457 é fragmento da #456 — remover
    mask457 = df["id"] == 457
    if mask457.any():
        relatorio["removidos"].append(
            {"id": 457, "motivo": "fragmento duplicado da questão 456"}
        )
        df = df[~mask457].reset_index(drop=True)

    for idx, row in df.iterrows():
        qid = int(row["id"])
        if qid not in IDS_ALVO or qid == 457:
            continue

        alteracoes: list[str] = []
        enunciado = ENUNCIADOS_IMT.get(qid, s(row["pergunta"]))
        blk, sim = bloco_por_enunciado(enunciado, blocks)

        if not blk:
            blk, sim = match_question(enunciado, blocks)
            if blk:
                blk = {"pergunta": blk["pergunta"], "opts": blk["opts"]}

        if blk:
            alteracoes = aplicar_bloco(df, idx, blk)

        manual = CORRECOES_MANUAIS.get(qid, {})
        for col, val in manual.items():
            if s(df.at[idx, col]) != val:
                df.at[idx, col] = val
                alteracoes.append(col)

        # #472: no IMT oficial só existem A e B — não inventar C/D
        if qid == 472:
            for letra in "CD":
                df.at[idx, f"opcao{letra}"] = ""

        antes_opcoes = opcoes_preenchidas(row)
        depois_opcoes = opcoes_preenchidas(df.loc[idx])
        entrada = {
            "id": qid,
            "match": round(sim, 3) if blk else 0,
            "opcoes_antes": antes_opcoes,
            "opcoes_depois": depois_opcoes,
            "alteracoes": alteracoes,
        }
        if alteracoes or depois_opcoes > antes_opcoes:
            relatorio["reparados"].append(entrada)
        else:
            relatorio["sem_alteracao"].append(entrada)

    df.to_excel(EXCEL, index=False)
    OUT.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()