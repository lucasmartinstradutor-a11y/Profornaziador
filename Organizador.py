import time
from datetime import datetime
import pandas as pd
import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(page_title="Painel de Aula", page_icon="👨‍🏫", layout="wide")

# CSS Customizado para um design mais refinado
st.markdown("""
<style>
    /* Cor de fundo principal */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Estilo dos cards */
    .card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 25px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 100%;
    }
    /* Estilo dos botões */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #1E88E5;
        color: #1E88E5;
        background-color: #FFFFFF;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #1565C0;
        color: white;
        background-color: #1E88E5;
    }
    /* Estilo do container da métrica do timer */
    div[data-testid="stMetric"] {
        background-color: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    /* Títulos */
    h1, h2, h3 {
        color: #263238;
    }
    /* Abas com fundo branco */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        border-bottom: 2px solid #1E88E5;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURAÇÕES GLOBAIS E ESTADO DA SESSÃO ---
SEGMENTOS_PADRAO = [
    {"nome": "Aquecimento", "min": 10},
    {"nome": "Exposição", "min": 25},
    {"nome": "Atividade", "min": 20},
    {"nome": "Fechamento", "min": 5},
]

def inicializar_estado():
    """Inicializa o estado da sessão se ainda não existir."""
    for key, value in {
        "rodando": False, "inicio_seg": 0.0, "duracao_seg": 0.0,
        "idx_seg": 0, "log": [], "presenca": {},
        "segmentos": SEGMENTOS_PADRAO
    }.items():
        if key not in st.session_state:
            st.session_state[key] = value

inicializar_estado()

def resetar_aula():
    """Reseta o estado do timer e do log para uma nova aula."""
    st.session_state.rodando = False
    st.session_state.inicio_seg = 0.0
    st.session_state.duracao_seg = 0.0
    st.session_state.idx_seg = 0
    st.session_state.log = []

# --- 3. SIDEBAR (BARRA LATERAL) ---
with st.sidebar:
    st.header("👨‍🏫 Configurações da Aula")
    
    curso = st.text_input("Disciplina", placeholder="Ex: História do Brasil I")
    data = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")

    st.markdown("---")
    st.header("👥 Lista de Presença")
    nomes = st.text_area("Cole a lista de alunos (um por linha):", height=150, placeholder="Aluno 1\nAluno 2\nAluno 3")
    
    lista_nomes = sorted([n.strip() for n in nomes.splitlines() if n.strip()])
    if lista_nomes:
        for n in lista_nomes:
            st.session_state.presenca.setdefault(n, False)
        for n in lista_nomes:
            st.session_state.presenca[n] = st.checkbox(n, value=st.session_state.presenca.get(n, False))

    col1, col2 = st.columns(2)
    if col1.button("📥 Baixar Presença"):
        if not st.session_state.presenca:
            st.warning("Nenhum aluno na lista.")
        else:
            dfp = pd.DataFrame(
                [{"data": data.strftime('%Y-%m-%d'), "curso": curso, "nome": n, "presente": p}
                 for n, p in st.session_state.presenca.items()]
            )
            st.download_button(
                "Clique para baixar", dfp.to_csv(index=False).encode("utf-8"),
                file_name=f"presenca_{curso}_{data.strftime('%Y-%m-%d')}.csv", mime="text/csv"
            )
    
    if col2.button("🧹 Limpar Lista"):
        st.session_state.presenca = {}
        st.rerun()


# --- 4. PAINEL PRINCIPAL ---
st.title("Painel do Dia de Aula")

# Card para Título e Tema da Aula
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_titulo, col_tema = st.columns(2)
    titulo_aula = col_titulo.text_input("Título da Aula", placeholder="Ex: A Era Vargas")
    tema_aula = col_tema.text_input("Tema da Aula", placeholder="Ex: Estado Novo e Populismo")
    st.markdown('</div>', unsafe_allow_html=True)


col_timer, col_notas = st.columns([1.1, 1])

with col_timer:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("⏱️ Timer da Aula")

        with st.expander("⚙️ Configurar Blocos da Aula"):
            segs_editados = []
            for i, seg in enumerate(st.session_state.segmentos):
                c1, c2 = st.columns([2, 1])
                nome = c1.text_input(f"Nome do bloco {i+1}", seg["nome"], key=f"seg_nome_{i}")
                minutos = c2.number_input("Minutos", 1, 180, seg["min"], key=f"seg_min_{i}")
                segs_editados.append({"nome": nome, "min": int(minutos)})
            st.session_state.segmentos = segs_editados

        idx_atual = st.session_state.idx_seg
        bloco_atual = st.session_state.segmentos[idx_atual]
        st.info(f"**Bloco atual:** {bloco_atual['nome']} — **Duração Prevista:** {bloco_atual['min']} min")

        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        if col_t1.button("▶️ Iniciar", disabled=st.session_state.rodando, use_container_width=True):
            st.session_state.rodando = True
            st.session_state.inicio_seg = time.time() - st.session_state.duracao_seg
            st.rerun()

        if col_t2.button("⏸️ Pausar", disabled=not st.session_state.rodando, use_container_width=True):
            st.session_state.rodando = False
            st.rerun()

        if col_t3.button("⏭️ Próximo", use_container_width=True):
            gasto = st.session_state.duracao_seg / 60
            st.session_state.log.append({
                "data": data.strftime('%Y-%m-%d'), "curso": curso, "titulo_aula": titulo_aula, "tema_aula": tema_aula,
                "tipo": "Bloco de Aula", "bloco": bloco_atual["nome"], "min_previstos": bloco_atual["min"],
                "min_gastos": round(gasto, 1), "conteudo": "", "timestamp": datetime.now().isoformat()
            })
            st.session_state.idx_seg = min(idx_atual + 1, len(st.session_state.segmentos) - 1)
            st.session_state.rodando = False
            st.session_state.inicio_seg = 0.0
            st.session_state.duracao_seg = 0.0
            st.rerun()
        
        if col_t4.button("🔄 Resetar", use_container_width=True):
            resetar_aula()
            st.rerun()

        if st.session_state.rodando:
            st.session_state.duracao_seg = time.time() - st.session_state.inicio_seg

        decorrido = int(st.session_state.duracao_seg)
        restante = max(0, bloco_atual["min"] * 60 - decorrido)
        mm, ss = divmod(restante, 60)
        
        st.metric("Tempo Restante", f"{mm:02d}:{ss:02d}")
        
        progresso = min(1.0, decorrido / (bloco_atual["min"] * 60) if bloco_atual["min"] > 0 else 0)
        st.progress(progresso)
        st.markdown('</div>', unsafe_allow_html=True)

with col_notas:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("📝 Bloco de Notas")

        tab1, tab2, tab3 = st.tabs(["Conteúdo", "Tarefas", "Trabalhos"])

        with tab1:
            conteudo = st.text_area("Anote pontos importantes do conteúdo:", height=150, key="conteudo_aula")
            if st.button("➕ Registrar Conteúdo"):
                if conteudo:
                    st.session_state.log.append({
                        "data": data.strftime('%Y-%m-%d'), "curso": curso, "titulo_aula": titulo_aula, "tema_aula": tema_aula,
                        "tipo": "Conteúdo", "bloco": bloco_atual["nome"], "conteudo": conteudo,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success("Conteúdo registrado no log!")
                else:
                    st.warning("Escreva algo para registrar.")

        with tab2:
            tarefa = st.text_area("Descreva tarefas para a turma:", height=150, key="tarefa_aula")
            if st.button("➕ Registrar Tarefa"):
                if tarefa:
                    st.session_state.log.append({
                        "data": data.strftime('%Y-%m-%d'), "curso": curso, "titulo_aula": titulo_aula, "tema_aula": tema_aula,
                        "tipo": "Tarefa", "bloco": "N/A", "conteudo": tarefa,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success("Tarefa registrada no log!")
                else:
                    st.warning("Descreva a tarefa para registrar.")

        with tab3:
            trabalho = st.text_area("Descreva trabalhos ou avaliações:", height=150, key="trabalho_aula")
            if st.button("➕ Registrar Trabalho"):
                if trabalho:
                    st.session_state.log.append({
                        "data": data.strftime('%Y-%m-%d'), "curso": curso, "titulo_aula": titulo_aula, "tema_aula": tema_aula,
                        "tipo": "Trabalho", "bloco": "N/A", "conteudo": trabalho,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success("Trabalho registrado no log!")
                else:
                    st.warning("Descreva o trabalho para registrar.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. VISUALIZAÇÃO E DOWNLOAD DO LOG ---
st.markdown("---")
st.header("🧾 Log da Aula")

if st.session_state.log:
    dflog = pd.DataFrame(st.session_state.log)
    colunas_visiveis = ['tipo', 'bloco', 'conteudo', 'min_previstos', 'min_gastos', 'titulo_aula', 'tema_aula']
    df_display = dflog[[col for col in colunas_visiveis if col in dflog.columns]]
    st.dataframe(df_display, use_container_width=True)
    
    st.download_button(
        "📥 Baixar Log Completo (CSV)",
        dflog.to_csv(index=False).encode("utf-8"),
        file_name=f"log_{curso}_{data.strftime('%Y-%m-%d')}.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhuma entrada no log ainda. Inicie a aula e registre notas para visualizar.")


# --- LÓGICA DE ATUALIZAÇÃO DO TIMER ---
if st.session_state.rodando:
    time.sleep(1)
    st.rerun()
