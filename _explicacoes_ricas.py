"""
Gera explicações pedagógicas para o banco CAM/IMT.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from _alinhar_imt import norm, s
from _aplicar_gabarito_testescam import sim_texto

BASE = Path(__file__).parent
EXCEL = BASE / "questoes sem rep.xlsx"
OUT = BASE / "_explicacoes_ricas.json"

PREFIXO_IMT = re.compile(r"^Resposta aceite no exame IMT[.:]?\s*", re.I)
RE_NUM = re.compile(r"\d+[\d\s.,]*")

FONTES = [
    BASE / "_questoes_full.json",
    BASE / "questoes_backup_antes_import_imt.xlsx",
    BASE / "questoes_backup_antes_reconstrucao.xlsx",
    BASE / "questoes_backup_antes_revisao.xlsx",
    BASE / "questoes_revisao.xlsx",
]

FRACA = re.compile(
    r"(esta alternativa responde corretamente|resposta aceite no exame imt|"
    r"não é a medida ou o procedimento|a questão exige aplicar|a questão incide sobre|"
    r"a questão testa conhecimentos|a questão trata do|a questão avalia|"
    r"a questão refere|a questão aborda|a resposta correta é a opção)",
    re.I,
)


def eh_fraca(texto: str) -> bool:
    t = s(texto)
    if not t:
        return True
    if len(t) < 70:
        return True
    return bool(FRACA.search(t))


def limpar_explicacao_fonte(texto: str) -> str:
    t = PREFIXO_IMT.sub("", s(texto)).strip()
    if t.lower().startswith("resposta aceite no exame imt"):
        t = PREFIXO_IMT.sub("", t).strip()
    return t


def carregar_fontes() -> dict[str, str]:
    por_texto: dict[str, str] = {}

    def registar(pergunta: str, explicacao: str):
        exp = limpar_explicacao_fonte(explicacao)
        if not exp or eh_fraca(exp):
            return
        k = norm(pergunta)
        if len(k) < 12:
            return
        if len(exp) > len(por_texto.get(k, "")):
            por_texto[k] = exp

    for path in FONTES:
        if not path.exists():
            continue
        if path.suffix == ".json":
            for item in json.loads(path.read_text(encoding="utf-8")):
                registar(item.get("pergunta", ""), item.get("explicacao", ""))
        else:
            df = pd.read_excel(path)
            if "pergunta" not in df.columns or "explicacao" not in df.columns:
                continue
            for _, row in df.iterrows():
                registar(row.get("pergunta", ""), row.get("explicacao", ""))
    return por_texto


def buscar_fonte(pergunta: str, fontes: dict[str, str]) -> str | None:
    k = norm(pergunta)
    if k in fontes:
        return fontes[k]
    melhor, sim, exp = None, 0.0, None
    for fk, fv in fontes.items():
        r = sim_texto(pergunta, fk)
        if r > sim:
            sim, melhor, exp = r, fk, fv
    if melhor and sim >= 0.88:
        return exp
    return None


def tipo_enunciado(pergunta: str) -> str:
    p = norm(pergunta)
    if any(x in p for x in ("incorreta", "indique a falsa", "afirmacao e falsa", "qual e falsa", "esta afirmacao e")):
        return "falsa"
    if any(x in p for x in ("verdadeira", "correta", "assinale", "indique a", "melhor se identifica")):
        return "verdadeira"
    if any(x in p for x in ("consiste", "denomina se", "e o transporte", "define se")):
        return "definicao"
    if any(x in p for x in ("tempo maximo", "prazo", "horas", "dias", "metros", "tonelad", "peso bruto")):
        return "limite"
    if any(x in p for x in ("deve", "devo", "procedimento", "diga o que", "em caso de")):
        return "procedimento"
    return "geral"


def opcoes_dict(row) -> dict[str, str]:
    return {L: s(row.get(f"opcao{L}")) for L in "ABCD" if s(row.get(f"opcao{L}"))}


def citar_opcao(texto: str, limite: int = 75) -> str:
    t = s(texto)
    return t if len(t) <= limite else t[: limite - 1] + "…"


# (padrão no enunciado normalizado, função geradora)
def _explicar_amaracao_laco(row, letra, opcao, _ops):
    return (
        "A amarração em laço prende a carga a um dos lados da carroçaria, formando um laço — "
        "método previsto no manual IMT de Acondicionamento de Carga (sec. 3.2.2). "
        f"A opção {letra}) descreve esse procedimento: {opcao}."
    )


def _explicar_telemovel(row, letra, opcao, _ops):
    return (
        "O Código da Estrada (art. 82.º) proíbe segurar ou manipular o telemóvel enquanto se conduz; "
        "o uso em viva-voz ou mãos-livres é o permitido. "
        f"Por isso {letra}) está correta: {opcao}."
    )


def _explicar_binario(row, letra, opcao, ops):
    return (
        "O binário do motor é o momento de rotação (torque) aplicado ao veículo. "
        "A opção A) refere-se à potência; a B) aproxima-se do conceito de binário, "
        "mas no gabarito IMT a resposta aceite é D) porque nenhuma das três primeiras definições "
        "descreve o binário de forma completa e isolada."
    )


def _explicar_carga_completa(row, letra, opcao, ops):
    return (
        "Transporte em regime de carga completa significa que o veículo é utilizado na totalidade "
        "da sua capacidade por um único expedidor (um cliente por serviço). "
        f"A opção {letra}) exprime isso. A opção A) descreve carga fracionada, "
        "em que vários expedidores partilham o mesmo veículo."
    )


def _explicar_alvara(row, letra, opcao, ops):
    return (
        "O alvará ou licença comunitária de transporte rodoviário de mercadorias por conta de outrem "
        "é pessoal e intransmissível — não passa com a venda da empresa ou dos veículos. "
        f"Daí a opção {letra}) ({opcao})."
    )


def _explicar_deflectores(row, letra, opcao, ops):
    return (
        "Quando o reboque/semi-reboque é mais alto que o trator, o ar turbulento aumenta o consumo. "
        "Os deflectores no tejadilho do trator orientam o fluxo de ar e "
        f"{opcao.lower().rstrip('.')}, poupando combustível. Aumentar a resistência aerodinâmica seria o efeito oposto."
    )


def _explicar_alimentacao_incorreta(row, letra, opcao, ops):
    return (
        "O enunciado pede a afirmação incorreta sobre alimentação do motorista. "
        "Horários de refeição irregulares prejudicam energia e concentração; "
        f"por isso {letra}) («{citar_opcao(opcao)}») é a única errada. "
        "Pequeno-almoço regular, evitar jejus prolongados e consumir peixe/carnes brancas são boas práticas."
    )


def _explicar_roubo_assalto(row, letra, opcao, ops):
    return (
        "Em roubo ou assalto à carga, o condutor deve preservar a segurança, avaliar danos e perdas, "
        "comunicar de imediato ao empregador e à polícia e colaborar no registo do incidente. "
        f"Isso corresponde a {letra}): {opcao}."
    )


def _explicar_reclamacao_todas(row, letra, opcao, ops):
    return (
        "Perante uma reclamação, o profissional deve ouvir, validar o sentimento do cliente, "
        "explicar a solução e agradecer o feedback. "
        "Como A), B) e C) são atitudes corretas isoladamente, "
        f"a resposta {letra}) resume que todas estão corretas."
    )


def _explicar_manobra_espelho(row, letra, opcao, ops):
    return (
        "Antes de qualquer deslocação lateral, o condutor deve observar o espelho, "
        "sinalizar a intenção, voltar a consultar o espelho e só então executar a manobra. "
        f"É a sequência «{opcao}» indicada em {letra})."
    )


def _explicar_pombos(row, letra, opcao, ops):
    return (
        "A Associação Columbófila transporta por conta própria, sem fins comerciais de transportador, "
        "num veículo cedido gratuitamente para uma largada de pombos-correio. "
        "Não se trata de exercício da atividade de transporte público de mercadorias; "
        f"por isso {letra}) está correta: {opcao}. "
        "Licenciamento ou autorização do IMT só seria exigido em transporte comercial."
    )


def _explicar_tempo_trabalho(row, letra, opcao, ops):
    return (
        "Para o condutor profissional, o tempo máximo de trabalho diário (condução + outras tarefas, "
        "incluindo pausas) é de 13 horas, podendo em casos excecionais chegar a 15 h. "
        f"O valor correto é {letra}): {opcao}."
    )


def _explicar_bilhetica(row, letra, opcao, ops):
    return (
        "A bilhética sem contacto permite validar títulos de transporte sem contacto físico prolongado, "
        "facilitando a fiscalização em bordo. "
        f"A afirmação verdadeira é {letra}): {opcao}."
    )


CONHECIMENTO: list[tuple[str, object]] = [
    ("amarração em laço", _explicar_amaracao_laco),
    ("amarração em laco", _explicar_amaracao_laco),
    ("telemóvel", _explicar_telemovel),
    ("telemovel", _explicar_telemovel),
    ("telefone ao volante", _explicar_telemovel),
    ("binário do motor", _explicar_binario),
    ("binario do motor", _explicar_binario),
    ("carga completa", _explicar_carga_completa),
    ("alvará ou licença comunitária", _explicar_alvara),
    ("alvara ou licenca comunitaria", _explicar_alvara),
    ("deflectores", _explicar_deflectores),
    ("semi reboques acoplados", _explicar_deflectores),
    ("alimentação saudável pode contribuir", _explicar_alimentacao_incorreta),
    ("afirmações está incorreta", _explicar_alimentacao_incorreta),
    ("roubo ou assalto", _explicar_roubo_assalto),
    ("reclamação do cliente", _explicar_reclamacao_todas),
    ("reclamacao do cliente", _explicar_reclamacao_todas),
    ("deslocação lateral", _explicar_manobra_espelho),
    ("deslocacao lateral", _explicar_manobra_espelho),
    ("bilhética sem contacto", _explicar_bilhetica),
    ("bilhetica sem contacto", _explicar_bilhetica),
    ("largada de pombos", _explicar_pombos),
    ("tempo máximo de trabalho diário", _explicar_tempo_trabalho),
    ("tempo maximo de trabalho diario", _explicar_tempo_trabalho),
]


def conhecimento_especifico(row, letra: str, opcao: str, ops: dict[str, str]) -> str | None:
    p = norm(s(row.get("pergunta")))
    for chave, fn in CONHECIMENTO:
        if chave in p:
            return fn(row, letra, opcao, ops)
    return None


def contraste_inteligente(pergunta: str, letra: str, opcao: str, ops: dict[str, str], tipo: str) -> str:
    return ""


def resumo_pergunta(pergunta: str, limite: int = 90) -> str:
    p = s(pergunta).strip()
    if p.endswith(":"):
        p = p[:-1]
    if len(p) > limite:
        p = p[: limite - 1].rsplit(" ", 1)[0] + "…"
    return p


def explicacao_por_tipo(pergunta: str, letra: str, opcao: str, ops: dict[str, str], tipo: str) -> str:
    resumo = resumo_pergunta(pergunta)

    if tipo == "falsa":
        base = (
            f"O enunciado pede a afirmação errada sobre «{resumo}». "
            f"{letra}) é a incorreta: {opcao}."
        )
    elif tipo == "definicao":
        base = (
            f"Na definição pedida («{resumo}»), o conceito correto é "
            f"{opcao} (opção {letra}))."
        )
    elif tipo == "limite" and RE_NUM.search(opcao):
        base = (
            f"Quanto a «{resumo}», o limite ou valor aplicável é "
            f"{opcao} ({letra}))."
        )
    elif tipo == "procedimento":
        base = (
            f"Na situação «{resumo}», o procedimento correto é "
            f"{opcao} (opção {letra}))."
        )
    elif "todas as outras" in opcao.lower() or "todas as anteriores" in opcao.lower():
        base = (
            f"Relativamente a «{resumo}», as alternativas anteriores são corretas em separado; "
            f"por isso {letra}) («{citar_opcao(opcao)}») é a resposta completa."
        )
    else:
        base = (
            f"Relativamente a «{resumo}», a resposta adequada é "
            f"{letra}): {opcao}."
        )

    return base + contraste_inteligente(pergunta, letra, opcao, ops, tipo)


def enriquecer_curta(row, texto: str) -> str:
    if len(s(texto)) >= 100:
        return texto
    letra = s(row.get("resposta_correta")).upper()
    opcao = s(row.get(f"opcao{letra}"))
    if not opcao:
        return texto
    complemento = explicacao_por_tipo(
        s(row.get("pergunta")), letra, opcao, opcoes_dict(row), tipo_enunciado(s(row.get("pergunta")))
    )
    if texto.lower() in complemento.lower():
        return complemento
    return f"{texto} {complemento}"


def gerar_explicacao(row, fontes: dict[str, str] | None = None) -> tuple[str, str]:
    pergunta = s(row.get("pergunta"))
    letra = s(row.get("resposta_correta")).upper()
    opcao = s(row.get(f"opcao{letra}"))
    exp_atual = limpar_explicacao_fonte(s(row.get("explicacao")))
    ops = opcoes_dict(row)

    if exp_atual and not eh_fraca(exp_atual) and len(exp_atual) >= 100:
        return exp_atual, "mantida"

    if fontes:
        restaurada = buscar_fonte(pergunta, fontes)
        if restaurada and not eh_fraca(restaurada):
            if len(restaurada) < 100:
                return enriquecer_curta(row, restaurada), "fonte_enriquecida"
            return restaurada, "fonte"

    if not opcao:
        return exp_atual or "Sem explicação disponível.", "vazia"

    especifica = conhecimento_especifico(row, letra, opcao, ops)
    if especifica:
        return especifica, "especifica"

    if exp_atual and not eh_fraca(exp_atual):
        return enriquecer_curta(row, exp_atual), "enriquecida"

    tipo = tipo_enunciado(pergunta)
    texto = explicacao_por_tipo(pergunta, letra, opcao, ops, tipo)
    return texto, "gerada"


def main():
    fontes = carregar_fontes()
    df = pd.read_excel(EXCEL)
    stats: dict[str, int] = {}

    for idx, row in df.iterrows():
        nova, modo = gerar_explicacao(row, fontes)
        stats[modo] = stats.get(modo, 0) + 1
        if s(row.get("explicacao")) != nova:
            df.at[idx, "explicacao"] = nova

    df.to_excel(EXCEL, index=False)
    fracas = sum(1 for _, r in df.iterrows() if eh_fraca(s(r.explicacao)))
    rel = {"total": len(df), "fracas_restantes": fracas, **stats}
    OUT.write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rel, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()