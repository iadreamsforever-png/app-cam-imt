import streamlit as st
import pandas as pd
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent

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

verificar_acesso()

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
        h3 { font-size: 1.1rem !important; line-height: 1.5 !important; }
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
        .stRadio > div {
            gap: 0.5rem;
        }
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
            height: 10px;
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
        .info-chip {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin: 0.35rem 0 0.85rem 0;
            font-size: 0.92rem;
            color: #334155;
            line-height: 1.5;
        }
        .info-chip strong { color: #0F172A; }
        .page-subtitle {
            color: #64748B;
            font-size: 0.95rem;
            margin-top: -0.5rem;
            margin-bottom: 1rem;
        }
        @media (max-width: 640px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            h1 { font-size: 1.45rem !important; }
            h3 { font-size: 1.05rem !important; }
            .stRadio > div[role="radiogroup"] {
                flex-direction: column !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def info_chip(texto):
    st.markdown(f'<div class="info-chip">{texto}</div>', unsafe_allow_html=True)

aplicar_estilo_mobile()

# ====================== CARREGAR PERGUNTAS DO EXCEL ======================
@st.cache_data
def carregar_perguntas():
    df = pd.read_excel(BASE_DIR / "questoes sem rep.xlsx")
    return df.to_dict("records")

perguntas = carregar_perguntas()

# ====================== ESTADO ======================
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "erros" not in st.session_state:
    st.session_state.erros = 0
if "perguntas_vistas" not in st.session_state:
    st.session_state.perguntas_vistas = set()

def ir_para(pagina):
    st.session_state.pagina = pagina
    st.rerun()

def limpar_simulacao():
    for key in ("simulacao_perguntas", "indice", "acertos_sim", "simulacao_respostas"):
        st.session_state.pop(key, None)

def limpar_pratica():
    for key in ("pratica_atual", "pratica_respondido", "pratica_acertou"):
        st.session_state.pop(key, None)

def processar_resposta(q, escolha):
    correta = q["resposta_correta"].lower()
    acertou = escolha.lower() == correta
    if acertou:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1
    st.session_state.perguntas_vistas.add(q["id"])
    return acertou

def mostrar_pergunta(q, key_prefix=""):
    st.markdown(f"### {q['pergunta']}")
    opcoes = ["A", "B", "C", "D"]
    return st.radio(
        "Escolha a resposta:",
        opcoes,
        format_func=lambda x: f"{x}) {q['opcao' + x]}",
        key=f"{key_prefix}escolha_{q['id']}",
        label_visibility="collapsed",
    )

def mostrar_feedback(q, acertou):
    if acertou:
        st.success("✅ Correto!")
    else:
        letra = q["resposta_correta"].upper()
        texto = q[f"opcao{letra}"]
        st.error(f"❌ Errado! A resposta correta é: **{letra}) {texto}**")
    st.info(q["explicacao"])

def mostrar_revisao_resposta(item, numero):
    q = item["pergunta"]
    escolha = item["escolha"].upper()
    correta = q["resposta_correta"].upper()
    acertou = item["acertou"]
    icone = "✅" if acertou else "❌"

    with st.expander(f"{icone} Questão {numero} — {q['pergunta'][:70]}{'...' if len(q['pergunta']) > 70 else ''}"):
        st.markdown(f"**{q['pergunta']}**")
        for letra in "ABCD":
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
        st.info(f"**Explicação:** {q['explicacao']}")

# ====================== TELA INICIAL ======================
if st.session_state.pagina == "inicio":
    st.title("🚛 Simulados CAM - IMT")
    st.markdown('<p class="page-subtitle">Preparação para o exame oficial do IMT</p>', unsafe_allow_html=True)

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

    if st.button("🚀 Simulação Completa (60 questões)", use_container_width=True, type="primary"):
        limpar_simulacao()
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
        st.rerun()

    if st.button("🔒 Terminar sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# ====================== SIMULAÇÃO COMPLETA ======================
elif st.session_state.pagina == "simulacao":
    st.header("🚀 Simulação Completa")

    if "simulacao_perguntas" not in st.session_state:
        total = min(60, len(perguntas))
        st.session_state.simulacao_perguntas = random.sample(perguntas, total)
        st.session_state.indice = 0
        st.session_state.acertos_sim = 0
        st.session_state.simulacao_respostas = []

    total_sim = len(st.session_state.simulacao_perguntas)

    if st.session_state.indice < total_sim:
        q = st.session_state.simulacao_perguntas[st.session_state.indice]

        st.progress((st.session_state.indice + 1) / total_sim)
        info_chip(f"<strong>Pergunta {st.session_state.indice + 1} de {total_sim}</strong>")

        escolha = mostrar_pergunta(q, key_prefix="sim_")

        if st.button("Responder", type="primary", use_container_width=True):
            acertou = processar_resposta(q, escolha)
            if acertou:
                st.session_state.acertos_sim += 1
            st.session_state.simulacao_respostas.append({
                "pergunta": q,
                "escolha": escolha,
                "acertou": acertou,
            })
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
            limpar_simulacao()
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
        acertos = sum(1 for r in respostas if r["acertou"])
        erros = len(respostas) - acertos
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", len(respostas))
        with col2:
            st.metric("Acertos", acertos)
        with col3:
            st.metric("Erros", erros)

        filtro_rev = st.radio(
            "Mostrar:",
            ["Todas", "Apenas erradas", "Apenas corretas"],
        )

        lista = respostas
        if filtro_rev == "Apenas erradas":
            lista = [r for r in respostas if not r["acertou"]]
        elif filtro_rev == "Apenas corretas":
            lista = [r for r in respostas if r["acertou"]]

        st.write(f"**{len(lista)}** questões")
        st.markdown("---")

        for numero, item in enumerate(respostas, 1):
            if item not in lista:
                continue
            mostrar_revisao_resposta(item, numero)

        st.markdown("---")
        if st.button("← Voltar ao Resultado", use_container_width=True):
            ir_para("simulacao")

        if st.button("Voltar ao Início", use_container_width=True):
            limpar_simulacao()
            ir_para("inicio")

# ====================== PRÁTICA LIVRE ======================
elif st.session_state.pagina == "pratica_livre":
    st.header("📝 Prática Livre")
    st.caption("Responde questões aleatórias sem limite de tempo.")

    filtro = st.radio(
        "Filtrar perguntas:",
        ["Todas", "Ainda não vistas", "Já vistas"],
    )

    pool = perguntas
    if filtro == "Ainda não vistas":
        pool = [p for p in perguntas if p["id"] not in st.session_state.perguntas_vistas]
    elif filtro == "Já vistas":
        pool = [p for p in perguntas if p["id"] in st.session_state.perguntas_vistas]

    mostrando_feedback = (
        st.session_state.get("pratica_respondido")
        and st.session_state.get("pratica_atual") is not None
    )

    if not pool and not mostrando_feedback:
        st.warning("Nenhuma pergunta disponível com este filtro.")
        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_pratica()
            ir_para("inicio")
    else:
        fora_do_filtro = (
            "pratica_atual" not in st.session_state
            or st.session_state.pratica_atual not in {p["id"] for p in pool}
        )
        if fora_do_filtro and not st.session_state.get("pratica_respondido"):
            if pool:
                st.session_state.pratica_atual = random.choice(pool)["id"]
                st.session_state.pratica_respondido = False
                st.session_state.pop("pratica_acertou", None)
            else:
                st.session_state.pop("pratica_atual", None)

        if st.session_state.get("pratica_atual") is not None:
            q = next(p for p in perguntas if p["id"] == st.session_state.pratica_atual)

            total_biblioteca = len(perguntas)
            faltam_responder = total_biblioteca - len(st.session_state.perguntas_vistas)

            info_chip(
                f"<strong>Questão #{q['id']}</strong> — {len(pool)} disponíveis no filtro atual"
            )
            info_chip(
                f"<strong>Faltam responder: {faltam_responder} de {total_biblioteca}</strong>"
            )

            escolha = mostrar_pergunta(q, key_prefix="prat_")

            if not st.session_state.get("pratica_respondido"):
                if st.button("Responder", type="primary", use_container_width=True):
                    st.session_state.pratica_acertou = processar_resposta(q, escolha)
                    st.session_state.pratica_respondido = True
                    st.rerun()
            else:
                mostrar_feedback(q, st.session_state.pratica_acertou)

                if st.button("Avançar →", type="primary", use_container_width=True):
                    st.session_state.pratica_respondido = False
                    st.session_state.pop("pratica_acertou", None)
                    if pool:
                        st.session_state.pratica_atual = random.choice(pool)["id"]
                    else:
                        st.session_state.pop("pratica_atual", None)
                    st.rerun()

        if st.button("← Voltar ao Início", use_container_width=True):
            limpar_pratica()
            ir_para("inicio")

# ====================== BIBLIOTECA ======================
elif st.session_state.pagina == "biblioteca":
    st.header("📚 Biblioteca de Questões")
    st.caption(f"{len(perguntas)} questões no total")

    busca = st.text_input("🔍 Pesquisar", placeholder="Palavras-chave da pergunta...")
    filtro_bib = st.selectbox("Estado", ["Todas", "Vistas", "Não vistas"])

    filtradas = perguntas
    if busca:
        termo = busca.lower()
        filtradas = [p for p in filtradas if termo in p["pergunta"].lower() or termo in p["explicacao"].lower()]
    if filtro_bib == "Vistas":
        filtradas = [p for p in filtradas if p["id"] in st.session_state.perguntas_vistas]
    elif filtro_bib == "Não vistas":
        filtradas = [p for p in filtradas if p["id"] not in st.session_state.perguntas_vistas]

    st.write(f"**{len(filtradas)}** questões encontradas")

    for q in filtradas:
        vista = "✅" if q["id"] in st.session_state.perguntas_vistas else "⬜"
        resposta = q["resposta_correta"].upper()
        with st.expander(f"{vista} #{q['id']} — {q['pergunta'][:80]}{'...' if len(q['pergunta']) > 80 else ''}"):
            st.markdown(f"**{q['pergunta']}**")
            for letra in "ABCD":
                prefixo = "✅ " if letra == resposta else "   "
                st.write(f"{prefixo}**{letra})** {q[f'opcao{letra}']}")
            st.info(f"**Explicação:** {q['explicacao']}")

    if st.button("← Voltar ao Início", use_container_width=True):
        ir_para("inicio")

st.caption("Simulados CAM IMT • Preparação para o exame oficial")