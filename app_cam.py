import json
import re
import time
import streamlit as st
import pandas as pd
import random
from pathlib import Path

from components.progress_store import progress_store

BASE_DIR = Path(__file__).parent
PROGRESSO_FICHEIRO = BASE_DIR / ".streamlit" / "progresso_cam.json"
PROGRESSO_STORAGE_KEY = "cam_imt_progresso_v1"

st.set_page_config(page_title="Simulados CAM - IMT", page_icon="🚛", layout="centered")

# ====================== ACESSO POR PALAVRA-PASSE ======================
def obter_senha():
    try:
        return st.secrets["auth"]["password"]
    except (KeyError, AttributeError, FileNotFoundError):
        return None

def verificar_acesso():
    if st.session_state.get("autenticado"):
        return True

    senha_correta = obter_senha()
    if not senha_correta:
        st.error("Palavra-passe não configurada.")
        st.info("Local: cria `.streamlit/secrets.toml` com `[auth]` e `password`. Online: Settings → Secrets no Streamlit Cloud.")
        st.stop()

    st.title("🚛 Simulados CAM - IMT")
    st.subheader("Acesso restrito")
    st.caption("Introduz a palavra-passe para entrar.")

    with st.form("login"):
        senha = st.text_input("Palavra-passe", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if entrar:
        if senha == senha_correta:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Palavra-passe incorreta.")
    st.stop()


def exportar_progresso() -> dict:
    vistas = st.session_state.get("perguntas_vistas", set())
    usadas = st.session_state.get("simulacao_usadas", set())
    return {
        "v": 1,
        "atualizado": time.time(),
        "acertos": int(st.session_state.get("acertos", 0)),
        "erros": int(st.session_state.get("erros", 0)),
        "perguntas_vistas": sorted(int(x) for x in vistas),
        "simulacao_usadas": sorted(int(x) for x in usadas),
    }


def aplicar_progresso(dados: dict):
    st.session_state.acertos = int(dados.get("acertos", 0))
    st.session_state.erros = int(dados.get("erros", 0))
    st.session_state.perguntas_vistas = set(int(x) for x in dados.get("perguntas_vistas", []))
    st.session_state.simulacao_usadas = set(int(x) for x in dados.get("simulacao_usadas", []))


def ler_progresso_ficheiro():
    if not PROGRESSO_FICHEIRO.exists():
        return None
    try:
        return json.loads(PROGRESSO_FICHEIRO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None


def gravar_progresso_ficheiro(dados: dict):
    PROGRESSO_FICHEIRO.parent.mkdir(parents=True, exist_ok=True)
    PROGRESSO_FICHEIRO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def escolher_progresso_mais_recente(*fontes):
    validas = [f for f in fontes if isinstance(f, dict) and "v" in f]
    if not validas:
        return None
    return max(validas, key=lambda f: float(f.get("atualizado", 0)))


def salvar_progresso():
    if not st.session_state.get("_progresso_carregado"):
        return
    dados = exportar_progresso()
    gravar_progresso_ficheiro(dados)
    progress_store(
        action="set",
        storage_key=PROGRESSO_STORAGE_KEY,
        value=json.dumps(dados, ensure_ascii=False),
    )


def limpar_progresso_persistido():
    if PROGRESSO_FICHEIRO.exists():
        PROGRESSO_FICHEIRO.unlink(missing_ok=True)
    progress_store(action="clear", storage_key=PROGRESSO_STORAGE_KEY)


def inicializar_progresso():
    if st.session_state.get("_progresso_carregado"):
        return

    ficheiro = ler_progresso_ficheiro()
    browser_raw = progress_store(action="get", storage_key=PROGRESSO_STORAGE_KEY, default=None)
    browser = None
    if browser_raw:
        try:
            browser = json.loads(browser_raw)
        except json.JSONDecodeError:
            browser = None

    dados = escolher_progresso_mais_recente(ficheiro, browser)
    if dados:
        aplicar_progresso(dados)
    else:
        tentativas = st.session_state.get("_progresso_tentativas", 0)
        if tentativas < 1:
            st.session_state._progresso_tentativas = tentativas + 1
            st.rerun()
        st.session_state.acertos = 0
        st.session_state.erros = 0
        st.session_state.perguntas_vistas = set()
        st.session_state.simulacao_usadas = set()

    st.session_state._progresso_carregado = True
    salvar_progresso()


verificar_acesso()
inicializar_progresso()

def aplicar_estilo_mobile():
    st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
            max-width: 720px;
        }
        h1 { font-size: 1.65rem !important; font-weight: 700 !important; }
        h2 { font-size: 1.35rem !important; font-weight: 600 !important; }
        p, label, .stMarkdown { font-size: 1rem; line-height: 1.55; }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 0.65rem 0.75rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetric"] label {
            font-size: 0.78rem !important;
            color: #64748B !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
        }
        .stButton > button {
            min-height: 48px;
            border-radius: 12px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1rem !important;
        }
        .stRadio > div { gap: 0.5rem; }
        .stRadio label {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 0.85rem 1rem !important;
            margin: 0.2rem 0;
            width: 100%;
            line-height: 1.45;
        }
        .stRadio label:hover { border-color: #2563EB; }
        div[data-testid="stProgress"] > div > div {
            height: 8px;
            border-radius: 999px;
        }
        details[data-testid="stExpander"] {
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            background: #FFFFFF;
            margin-bottom: 0.5rem;
        }
        details[data-testid="stExpander"] summary {
            padding: 0.85rem 1rem;
            font-size: 0.95rem;
        }
        .titulo-discreto {
            color: #94A3B8;
            font-size: 0.72rem;
            font-weight: 500;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin: 0 0 0.35rem 0;
        }
        .meta-discreto {
            color: #94A3B8;
            font-size: 0.72rem;
            text-align: center;
            margin: 0.1rem 0 0.35rem 0;
            line-height: 1.4;
        }
        .questao-texto {
            font-size: 1.15rem;
            font-weight: 600;
            color: #0F172A;
            line-height: 1.55;
            text-align: center;
            margin: 1rem 0 1.25rem 0;
            padding: 0 0.25rem;
        }
        .page-subtitle {
            color: #64748B;
            font-size: 0.95rem;
            margin-top: -0.5rem;
            margin-bottom: 1rem;
        }
        .element-container:has(.bloco-opcoes) + .element-container div[data-testid="stRadio"] label {
            background: #FFFFFF;
            border: 1.5px solid #E2E8F0;
            border-radius: 14px;
            padding: 1rem 1.1rem !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
        }
        @media (max-width: 640px) {
            .block-container {
                padding-top: 0.75rem;
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            h1 { font-size: 1.45rem !important; }
            .titulo-discreto {
                font-size: 0.62rem;
                margin-bottom: 0.2rem;
            }
            .meta-discreto {
                font-size: 0.62rem;
                color: #CBD5E1;
            }
            .questao-texto {
                font-size: 1.12rem;
                margin: 1.75rem 0 1.35rem 0;
                padding: 0 0.15rem;
            }
            .element-container:has(.bloco-opcoes) + .element-container div[data-testid="stRadio"] {
                margin-top: 0.25rem;
            }
            .element-container:has(.bloco-opcoes) + .element-container div[data-testid="stRadio"] label {
                padding: 1.05rem 1.15rem !important;
                font-size: 0.98rem !important;
                margin: 0.35rem 0 !important;
            }
            .element-container:has(.bloco-opcoes) + .element-container div[data-testid="stRadio"] label p {
                font-size: 0.98rem !important;
                line-height: 1.5 !important;
            }
            div[data-testid="stProgress"] {
                opacity: 0.45;
                margin-bottom: 0.15rem !important;
            }
            div[data-testid="stProgress"] > div > div {
                height: 4px;
            }
            [data-testid="stPopover"] button {
                min-height: 28px !important;
                padding: 0.15rem 0.55rem !important;
                font-size: 0.75rem !important;
                color: #94A3B8 !important;
                background: transparent !important;
                border: 1px solid #E2E8F0 !important;
            }
            .stButton > button[kind="secondary"] {
                background: transparent !important;
                border: none !important;
                color: #94A3B8 !important;
                min-height: 34px !important;
                font-size: 0.78rem !important;
                box-shadow: none !important;
            }
            .stButton > button[data-testid="baseButton-primary"] {
                margin-top: 0.75rem;
            }
            .stRadio > div[role="radiogroup"] {
                flex-direction: column !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def titulo_discreto(texto):
    st.markdown(f'<p class="titulo-discreto">{texto}</p>', unsafe_allow_html=True)

def meta_linha(texto):
    st.markdown(f'<p class="meta-discreto">{texto}</p>', unsafe_allow_html=True)

aplicar_estilo_mobile()

# ====================== CARREGAR PERGUNTAS DO EXCEL ======================
EXCEL_QUESTOES = BASE_DIR / "questoes sem rep.xlsx"
SIMULACAO_TOTAL = 60
BIB_PAGE_SIZE = 50
CACHE_VERSION = 8


def campo(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    texto = str(valor).strip()
    return "" if texto.lower() == "nan" else texto


def opcoes_preenchidas(q) -> int:
    return sum(1 for letra in "ABCD" if campo(q.get(f"opcao{letra}")))


def letras_com_opcao(q) -> list[str]:
    return [letra for letra in "ABCD" if campo(q.get(f"opcao{letra}"))]


_RE_EXEMPLO = re.compile(r"\s*Por exemplo,.*$", re.I | re.S)
_RE_ALT_CORRETAS = re.compile(
    r"\s*As alternativas .* são afirmações corretas ou recomendadas\.?",
    re.I | re.S,
)


def _limpar_explicacao(exp: str) -> str:
    t = campo(exp)
    for pat in (_RE_EXEMPLO, _RE_ALT_CORRETAS):
        t = pat.sub("", t).strip()
    return t


def explicacao_util(q) -> str:
    """Usa a explicação do Excel; fallback simples se estiver vazia."""
    exp = _limpar_explicacao(campo(q.get("explicacao")))
    if exp and "esta alternativa responde corretamente" not in exp.lower():
        return exp

    letra = campo(q.get("resposta_correta")).upper()
    opcao = campo(q.get(f"opcao{letra}"))
    if opcao:
        return f"A resposta correta é **{letra})** {opcao}."
    return exp or "Sem explicação disponível para esta questão."


def normalizar_questao(q: dict) -> dict:
    out = dict(q)
    for chave in ("pergunta", "explicacao", "resposta_correta", "fonte_imt", "status_revisao"):
        if chave in out:
            out[chave] = campo(out[chave])
    for letra in "ABCD":
        out[f"opcao{letra}"] = campo(out.get(f"opcao{letra}"))
    if out.get("resposta_correta"):
        out["resposta_correta"] = out["resposta_correta"].lower()
    return out


def pergunta_funcional(q) -> bool:
    """Pergunta utilizável em simulado, prática e biblioteca."""
    if not resposta_valida(q):
        return False
    if len(campo(q.get("pergunta")).split()) < 3:
        return False
    letra = campo(q.get("resposta_correta")).upper()
    if not campo(q.get(f"opcao{letra}")):
        return False
    return opcoes_preenchidas(q) >= 2


def deduplicar_perguntas(records):
    """Garante uma única entrada por id e por texto de pergunta."""
    por_id = {}
    for r in records:
        qid = r.get("id")
        if qid is None:
            continue
        por_id[qid] = r

    unicas = []
    textos_vistos = set()
    for r in por_id.values():
        texto = str(r.get("pergunta", "")).strip().lower()
        if not texto or texto in textos_vistos:
            continue
        textos_vistos.add(texto)
        unicas.append(r)
    return unicas


def criar_conjunto_simulacao(pool, excluir_ids=None, total=SIMULACAO_TOTAL):
    """Sorteia questões únicas; exclui as já usadas em simulações anteriores."""
    excluir = excluir_ids or set()
    pool = [q for q in pool if resposta_valida(q) and q.get("id") not in excluir]
    unicas = deduplicar_perguntas(pool)
    n = min(total, len(unicas))
    if n <= 0:
        return []
    return random.sample(unicas, n)


def _excel_fingerprint():
    stt = EXCEL_QUESTOES.stat()
    return (stt.st_mtime_ns, stt.st_size)


@st.cache_data
def carregar_perguntas(excel_mtime_ns, excel_size, cache_version):
    df = pd.read_excel(EXCEL_QUESTOES)
    records = [normalizar_questao(r) for r in df.to_dict("records")]
    return deduplicar_perguntas(records)


def obter_perguntas():
    if not EXCEL_QUESTOES.exists():
        return []
    mtime_ns, size = _excel_fingerprint()
    fp = (mtime_ns, size)
    if st.session_state.get("_excel_fp") != fp:
        carregar_perguntas.clear()
        st.session_state._excel_fp = fp
    return carregar_perguntas(mtime_ns, size, CACHE_VERSION)


def resposta_valida(q):
    return str(q.get("resposta_correta", "")).strip().lower() in list("abcd")


def obter_perguntas_jogaveis(pool=None):
    base = pool if pool is not None else obter_perguntas()
    return [q for q in base if resposta_valida(q)]


def obter_perguntas_funcionais(pool=None):
    base = pool if pool is not None else obter_perguntas()
    return [q for q in base if pergunta_funcional(q)]


# ====================== ESTADO ======================
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "erros" not in st.session_state:
    st.session_state.erros = 0
if "perguntas_vistas" not in st.session_state:
    st.session_state.perguntas_vistas = set()
if "simulacao_usadas" not in st.session_state:
    st.session_state.simulacao_usadas = set()

def ir_para(pagina):
    st.session_state.pagina = pagina
    st.rerun()

def limpar_simulacao():
    for key in ("simulacao_perguntas", "indice", "acertos_sim", "simulacao_respostas"):
        st.session_state.pop(key, None)


def iniciar_simulacao():
    """Nova simulação com questões ainda não usadas em simulações anteriores."""
    limpar_simulacao()
    pool = obter_perguntas_funcionais()
    usadas = st.session_state.simulacao_usadas
    st.session_state.simulacao_perguntas = criar_conjunto_simulacao(pool, excluir_ids=usadas)
    for q in st.session_state.simulacao_perguntas:
        usadas.add(q["id"])
    st.session_state.indice = 0
    st.session_state.acertos_sim = 0
    st.session_state.simulacao_respostas = []
    salvar_progresso()

def limpar_pratica():
    for key in (
        "pratica_atual", "pratica_respondido", "pratica_acertou",
        "pratica_historico", "pratica_rever_indice", "pratica_sessao_completa",
    ):
        st.session_state.pop(key, None)


def ids_pratica_sessao(historico, atual_id=None):
    """IDs já mostrados na sessão atual de prática livre."""
    ids = {item["pergunta"]["id"] for item in historico}
    if atual_id is not None:
        ids.add(atual_id)
    return ids


def pool_pratica_disponivel(pool, historico, atual_id=None):
    usadas = ids_pratica_sessao(historico, atual_id)
    return [p for p in pool if p["id"] not in usadas]


def escolher_proxima_pratica(pool, historico, atual_id=None):
    """Sorteia próxima questão sem repetir as já vistas nesta sessão."""
    disponiveis = pool_pratica_disponivel(pool, historico, atual_id)
    if not disponiveis:
        return None
    return random.choice(disponiveis)["id"]


def processar_resposta(q, escolha):
    correta = q["resposta_correta"].lower()
    acertou = escolha.lower() == correta
    if acertou:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1
    st.session_state.perguntas_vistas.add(q["id"])
    salvar_progresso()
    return acertou

def atualizar_estatisticas_global(q, acertou, reverso=False):
    if reverso:
        if acertou:
            st.session_state.acertos = max(0, st.session_state.acertos - 1)
        else:
            st.session_state.erros = max(0, st.session_state.erros - 1)
    else:
        if acertou:
            st.session_state.acertos += 1
        else:
            st.session_state.erros += 1
        st.session_state.perguntas_vistas.add(q["id"])

def registar_resposta_simulacao(q, escolha, indice):
    acertou = escolha.lower() == q["resposta_correta"].lower()
    respostas = st.session_state.simulacao_respostas

    while len(respostas) <= indice:
        respostas.append(None)

    anterior = respostas[indice]
    if anterior is not None:
        if anterior["acertou"]:
            st.session_state.acertos_sim -= 1
        atualizar_estatisticas_global(q, anterior["acertou"], reverso=True)
        if acertou:
            st.session_state.acertos += 1
        else:
            st.session_state.erros += 1
    else:
        atualizar_estatisticas_global(q, acertou)

    respostas[indice] = {"pergunta": q, "escolha": escolha, "acertou": acertou}
    if acertou:
        st.session_state.acertos_sim += 1

    salvar_progresso()
    return acertou

def mostrar_pergunta(q, key_suffix="", escolha_previa=None):
    st.markdown(f'<p class="questao-texto">{q["pergunta"]}</p>', unsafe_allow_html=True)
    st.markdown('<div class="bloco-opcoes"></div>', unsafe_allow_html=True)
    opcoes = letras_com_opcao(q) or ["A", "B", "C", "D"]
    index = None
    if escolha_previa:
        prev = str(escolha_previa).upper()
        if prev in opcoes:
            index = opcoes.index(prev)
    return st.radio(
        "Escolha a resposta:",
        opcoes,
        index=index,
        format_func=lambda x: f"{x}) {q['opcao' + x]}",
        key=f"escolha_{key_suffix}",
        label_visibility="collapsed",
    )

def mostrar_resposta_escolhida(q, escolha):
    letra = str(escolha).upper()
    st.markdown(f"**A tua resposta:** {letra}) {q[f'opcao{letra}']}")

def mostrar_feedback(q, acertou):
    if acertou:
        st.success("✅ Correto!")
    else:
        letra = q["resposta_correta"].upper()
        texto = q[f"opcao{letra}"]
        st.error(f"❌ Errado! A resposta correta é: **{letra}) {texto}**")
    st.info(explicacao_util(q))

def mostrar_revisao_resposta(item, numero):
    q = item["pergunta"]
    escolha = item["escolha"].upper()
    correta = q["resposta_correta"].upper()
    acertou = item["acertou"]
    icone = "✅" if acertou else "❌"

    with st.expander(f"{icone} Questão {numero} — {q['pergunta'][:70]}{'...' if len(q['pergunta']) > 70 else ''}"):
        st.markdown(f"**{q['pergunta']}**")
        for letra in letras_com_opcao(q):
            if letra == correta:
                prefixo = "✅ "
            elif letra == escolha and not acertou:
                prefixo = "❌ "
            else:
                prefixo = "   "
            st.write(f"{prefixo}**{letra})** {q[f'opcao{letra}']}")
        if acertou:
            st.success(f"A tua resposta: **{escolha})** {q[f'opcao{escolha}']} — Correto!")
        else:
            st.error(f"A tua resposta: **{escolha})** {q[f'opcao{escolha}']}")
            st.success(f"Resposta correta: **{correta})** {q[f'opcao{correta}']}")
        st.info(f"**Explicação:** {explicacao_util(q)}")

# ====================== TELA INICIAL ======================
if st.session_state.pagina == "inicio":
    st.title("🚛 Simulados CAM - IMT")
    st.markdown(
        '<p class="page-subtitle">Preparação para o exame CAM do IMT — mercadorias e passageiros. '
        'Respostas alinhadas com o que o IMT aceita no exame.</p>',
        unsafe_allow_html=True,
    )
    funcionais = obter_perguntas_funcionais()
    usadas_sim = st.session_state.simulacao_usadas
    restantes_sim = len([q for q in funcionais if q["id"] not in usadas_sim])
    n_sim = min(SIMULACAO_TOTAL, restantes_sim)
    st.caption(
        f"Base: {len(funcionais)} questões funcionais · "
        f"{restantes_sim} ainda não usadas em simulações"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Perguntas vistas", len(st.session_state.perguntas_vistas))
    with col2:
        st.metric("Acertos", st.session_state.acertos)
    with col3:
        st.metric("Erros", st.session_state.erros)

    total_respostas = st.session_state.acertos + st.session_state.erros
    if total_respostas > 0:
        taxa = (st.session_state.acertos / total_respostas) * 100
        st.progress(st.session_state.acertos / total_respostas)
        st.caption(f"Taxa de acerto global: {taxa:.1f}%")

    st.markdown("---")

    if st.button(
        f"🚀 Simulação Completa ({n_sim} questões)",
        use_container_width=True,
        type="primary",
        disabled=n_sim == 0,
    ):
        iniciar_simulacao()
        ir_para("simulacao")

    if st.button("📝 Prática Livre", use_container_width=True):
        limpar_pratica()
        ir_para("pratica_livre")

    if st.button("📚 Biblioteca de Questões", use_container_width=True):
        ir_para("biblioteca")

    st.markdown("---")
    if st.button("🔄 Reiniciar estatísticas", use_container_width=True):
        st.session_state.acertos = 0
        st.session_state.erros = 0
        st.session_state.perguntas_vistas = set()
        st.session_state.simulacao_usadas = set()
        limpar_progresso_persistido()
        salvar_progresso()
        st.rerun()

    if st.button("🔒 Terminar sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# ====================== SIMULAÇÃO COMPLETA ======================
elif st.session_state.pagina == "simulacao":
    if "simulacao_perguntas" not in st.session_state:
        iniciar_simulacao()

    total_sim = len(st.session_state.simulacao_perguntas)

    if total_sim == 0:
        st.error(
            "Já utilizaste todas as questões em simulações. "
            "Reinicia as estatísticas no início para voltar a sortear o banco completo."
        )
        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_simulacao()
            ir_para("inicio")
        st.stop()

    if st.session_state.indice < total_sim:
        idx = st.session_state.indice
        q = st.session_state.simulacao_perguntas[idx]
        respostas = st.session_state.simulacao_respostas
        resposta_previa = respostas[idx] if idx < len(respostas) and respostas[idx] else None

        titulo_discreto("Simulação completa")
        meta_linha(f"Pergunta {idx + 1} de {total_sim}")
        st.progress((idx + 1) / total_sim)

        escolha_prev = resposta_previa["escolha"] if resposta_previa else None
        escolha = mostrar_pergunta(q, key_suffix=f"sim_{idx}", escolha_previa=escolha_prev)

        col_voltar, col_responder = st.columns(2)
        with col_voltar:
            if idx > 0 and st.button("← Anterior", use_container_width=True):
                st.session_state.indice -= 1
                st.rerun()
        with col_responder:
            if st.button("Responder", type="primary", use_container_width=True):
                registar_resposta_simulacao(q, escolha, idx)
                st.session_state.indice += 1
                st.rerun()

    else:
        st.balloons()
        percent = (st.session_state.acertos_sim / total_sim) * 100
        st.header("🎯 Resultado Final")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Acertos", st.session_state.acertos_sim)
        with col2:
            st.metric("Erros", total_sim - st.session_state.acertos_sim)
        with col3:
            st.metric("Percentagem", f"{percent:.1f}%")

        if percent >= 60:
            st.success("✅ APROVADO — Necessário mínimo de 60%")
        else:
            st.error("❌ REPROVADO — Necessário mínimo de 60%")

        if st.button("📋 Rever Questões Respondidas", type="primary", use_container_width=True):
            ir_para("revisao_sim")

        if st.button("🔄 Nova Simulação", use_container_width=True):
            iniciar_simulacao()
            st.rerun()

        if st.button("Voltar ao Início", use_container_width=True):
            limpar_simulacao()
            ir_para("inicio")

    if st.session_state.indice < total_sim:
        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_simulacao()
            ir_para("inicio")

# ====================== REVISÃO DA SIMULAÇÃO ======================
elif st.session_state.pagina == "revisao_sim":
    st.header("📋 Revisão da Simulação")

    respostas = st.session_state.get("simulacao_respostas", [])
    if not respostas:
        st.warning("Nenhuma simulação concluída para rever.")
        if st.button("← Voltar ao Início", use_container_width=True):
            ir_para("inicio")
    else:
        respostas_validas = [r for r in respostas if r is not None]
        acertos = sum(1 for r in respostas_validas if r["acertou"])
        erros = len(respostas_validas) - acertos
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(respostas))
        with col2:
            st.metric("Acertos", acertos)
        with col3:
            st.metric("Erros", erros)

        with st.popover("⋯ filtro"):
            filtro_rev = st.radio(
                "Mostrar:",
                ["Todas", "Apenas erradas", "Apenas corretas"],
            )

        lista = respostas_validas
        if filtro_rev == "Apenas erradas":
            lista = [r for r in respostas_validas if not r["acertou"]]
        elif filtro_rev == "Apenas corretas":
            lista = [r for r in respostas_validas if r["acertou"]]

        st.write(f"**{len(lista)}** questões")
        st.markdown("---")

        numero = 0
        for item in respostas:
            if item is None or item not in lista:
                continue
            numero += 1
            mostrar_revisao_resposta(item, numero)

        st.markdown("---")
        if st.button("← Voltar ao Resultado", use_container_width=True):
            ir_para("simulacao")

        if st.button("Voltar ao Início", use_container_width=True):
            limpar_simulacao()
            ir_para("inicio")

# ====================== PRÁTICA LIVRE ======================
elif st.session_state.pagina == "pratica_livre":
    if "pratica_historico" not in st.session_state:
        st.session_state.pratica_historico = []

    col_topo, col_filtro = st.columns([5, 1])
    with col_topo:
        titulo_discreto("Prática livre")
    with col_filtro:
        with st.popover("⋯"):
            filtro = st.radio(
                "Filtrar perguntas:",
                ["Todas", "Ainda não vistas", "Já vistas"],
            )

    pool = obter_perguntas_funcionais()
    banco = obter_perguntas()
    if filtro == "Ainda não vistas":
        pool = [p for p in pool if p["id"] not in st.session_state.perguntas_vistas]
    elif filtro == "Já vistas":
        pool = [p for p in pool if p["id"] in st.session_state.perguntas_vistas]

    historico = st.session_state.pratica_historico
    em_revisao = st.session_state.get("pratica_rever_indice") is not None

    mostrando_feedback = (
        st.session_state.get("pratica_respondido")
        and st.session_state.get("pratica_atual") is not None
        and not em_revisao
    )

    disponiveis_sessao = pool_pratica_disponivel(pool, historico)
    sessao_completa = (
        bool(pool)
        and not disponiveis_sessao
        and bool(historico)
        and not mostrando_feedback
        and not em_revisao
    )

    if sessao_completa or st.session_state.get("pratica_sessao_completa"):
        st.success(
            f"Completaste as **{len(historico)}** questões deste filtro nesta sessão, "
            "sem repetições."
        )
        if st.button("🔄 Reiniciar prática", use_container_width=True, type="primary"):
            limpar_pratica()
            ir_para("pratica_livre")
        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_pratica()
            ir_para("inicio")
    elif not pool and not mostrando_feedback and not em_revisao:
        st.warning("Nenhuma pergunta disponível com este filtro.")
        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_pratica()
            ir_para("inicio")
    else:
        if em_revisao:
            rev_idx = st.session_state.pratica_rever_indice
            item = historico[rev_idx]
            q = item["pergunta"]

            meta_linha(
                f"Revisão {rev_idx + 1} de {len(historico)} · "
                f"Questão #{q['id']}"
            )

            st.markdown(f'<p class="questao-texto">{q["pergunta"]}</p>', unsafe_allow_html=True)
            mostrar_resposta_escolhida(q, item["escolha"])
            mostrar_feedback(q, item["acertou"])

            col_ant, col_seg, col_cont = st.columns(3)
            with col_ant:
                if rev_idx > 0 and st.button("← Anterior", use_container_width=True):
                    st.session_state.pratica_rever_indice = rev_idx - 1
                    st.rerun()
            with col_seg:
                if rev_idx < len(historico) - 1 and st.button("Seguinte →", use_container_width=True):
                    st.session_state.pratica_rever_indice = rev_idx + 1
                    st.rerun()
            with col_cont:
                if st.button("Continuar", type="primary", use_container_width=True):
                    st.session_state.pop("pratica_rever_indice", None)
                    st.rerun()
        else:
            fora_do_filtro = (
                "pratica_atual" not in st.session_state
                or st.session_state.pratica_atual not in {p["id"] for p in pool}
            )
            if fora_do_filtro and not st.session_state.get("pratica_respondido"):
                proxima = escolher_proxima_pratica(pool, historico)
                if proxima is not None:
                    st.session_state.pratica_atual = proxima
                    st.session_state.pratica_respondido = False
                    st.session_state.pop("pratica_acertou", None)
                    st.session_state.pop("pratica_sessao_completa", None)
                else:
                    st.session_state.pop("pratica_atual", None)
                    st.session_state.pratica_sessao_completa = True
                    st.rerun()

            if st.session_state.get("pratica_atual") is not None:
                q = next(p for p in banco if p["id"] == st.session_state.pratica_atual)

                total_jog = len(pool)
                faltam_responder = total_jog - len(st.session_state.perguntas_vistas)

                vistas_sessao = len(ids_pratica_sessao(historico, q["id"]))
                meta_linha(
                    f"Questão #{q['id']} · {vistas_sessao}/{len(pool)} nesta sessão · "
                    f"faltam {faltam_responder}/{total_jog} no filtro"
                )

                escolha = mostrar_pergunta(q, key_suffix=f"prat_{q['id']}")

                if not st.session_state.get("pratica_respondido"):
                    col_voltar, col_resp = st.columns(2)
                    with col_voltar:
                        if historico and st.button("← Rever anteriores", use_container_width=True):
                            st.session_state.pratica_rever_indice = len(historico) - 1
                            st.rerun()
                    with col_resp:
                        if st.button("Responder", type="primary", use_container_width=True):
                            acertou = processar_resposta(q, escolha)
                            st.session_state.pratica_acertou = acertou
                            st.session_state.pratica_respondido = True
                            historico.append({
                                "pergunta": q,
                                "escolha": escolha,
                                "acertou": acertou,
                            })
                            st.rerun()
                else:
                    mostrar_feedback(q, st.session_state.pratica_acertou)

                    col_voltar, col_avancar = st.columns(2)
                    with col_voltar:
                        if historico and st.button("← Rever anteriores", use_container_width=True):
                            st.session_state.pratica_rever_indice = len(historico) - 1
                            st.rerun()
                    with col_avancar:
                        if st.button("Avançar →", type="primary", use_container_width=True):
                            st.session_state.pratica_respondido = False
                            st.session_state.pop("pratica_acertou", None)
                            proxima = escolher_proxima_pratica(
                                pool, historico, atual_id=q["id"]
                            )
                            if proxima is not None:
                                st.session_state.pratica_atual = proxima
                                st.session_state.pop("pratica_sessao_completa", None)
                            else:
                                st.session_state.pop("pratica_atual", None)
                                st.session_state.pratica_sessao_completa = True
                            st.rerun()

        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_pratica()
            ir_para("inicio")

# ====================== BIBLIOTECA ======================
elif st.session_state.pagina == "biblioteca":
    funcionais = obter_perguntas_funcionais()

    st.header("📚 Biblioteca de Questões")
    col_cap, col_atualizar = st.columns([4, 1])
    with col_cap:
        total_pag = max(1, (len(funcionais) + BIB_PAGE_SIZE - 1) // BIB_PAGE_SIZE)
        st.caption(
            f"{len(funcionais)} questões · {BIB_PAGE_SIZE} por página · {total_pag} páginas"
        )
    with col_atualizar:
        if st.button("↻", help="Atualizar questões"):
            carregar_perguntas.clear()
            st.session_state.pop("_excel_fp", None)
            st.session_state.bib_pagina = 1
            st.rerun()

    busca = st.text_input("🔍 Pesquisar", placeholder="Palavras-chave da pergunta...")
    filtro_bib = st.selectbox("Estado", ["Todas", "Vistas", "Não vistas"])

    filtradas = list(funcionais)
    if busca:
        termo = busca.lower()
        filtradas = [
            p for p in filtradas
            if termo in campo(p.get("pergunta")).lower()
            or termo in campo(p.get("explicacao")).lower()
        ]
    if filtro_bib == "Vistas":
        filtradas = [p for p in filtradas if p["id"] in st.session_state.perguntas_vistas]
    elif filtro_bib == "Não vistas":
        filtradas = [p for p in filtradas if p["id"] not in st.session_state.perguntas_vistas]

    total_filtradas = len(filtradas)
    total_paginas = max(1, (total_filtradas + BIB_PAGE_SIZE - 1) // BIB_PAGE_SIZE)
    if "bib_pagina" not in st.session_state:
        st.session_state.bib_pagina = 1
    st.session_state.bib_pagina = max(1, min(st.session_state.bib_pagina, total_paginas))

    st.write(f"**{total_filtradas}** questões · página **{st.session_state.bib_pagina}** de **{total_paginas}**")

    col_ant, col_num, col_seg = st.columns([1, 2, 1])
    with col_ant:
        if st.button("← Anterior", disabled=st.session_state.bib_pagina <= 1, use_container_width=True):
            st.session_state.bib_pagina -= 1
            st.rerun()
    with col_num:
        st.session_state.bib_pagina = st.number_input(
            "Página",
            min_value=1,
            max_value=total_paginas,
            value=st.session_state.bib_pagina,
            step=1,
            label_visibility="collapsed",
        )
    with col_seg:
        if st.button("Seguinte →", disabled=st.session_state.bib_pagina >= total_paginas, use_container_width=True):
            st.session_state.bib_pagina += 1
            st.rerun()

    inicio = (st.session_state.bib_pagina - 1) * BIB_PAGE_SIZE
    pagina_itens = filtradas[inicio : inicio + BIB_PAGE_SIZE]

    for q in pagina_itens:
        vista = "✅" if q["id"] in st.session_state.perguntas_vistas else "⬜"
        jogavel = resposta_valida(q)
        gabarito = "📝" if jogavel else "⏳"
        resposta = campo(q.get("resposta_correta")).upper()
        pergunta = campo(q.get("pergunta"))
        titulo = f"{vista}{gabarito} #{q['id']} — {pergunta[:80]}{'...' if len(pergunta) > 80 else ''}"
        with st.expander(titulo):
            st.markdown(f"**{pergunta}**")
            for letra in "ABCD":
                opcao = campo(q.get(f"opcao{letra}"))
                if not opcao:
                    continue
                prefixo = "✅ " if jogavel and letra == resposta else "   "
                st.write(f"{prefixo}**{letra})** {opcao}")
            if jogavel:
                exp = explicacao_util(q)
                if exp:
                    st.info(f"**Explicação:** {exp}")
            elif not jogavel:
                st.warning("Gabarito IMT pendente — disponível para consulta, não entra em simulados.")

    if st.button("← Voltar ao Início", use_container_width=True):
        ir_para("inicio")

salvar_progresso()
st.caption("Simulados CAM IMT • Preparação para o exame oficial")