import time
from datetime import datetime
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(page_title="Painel de Aula", page_icon="👨‍🏫", layout="wide")

# CSS Customizado para melhorar o layout e as cores
st.markdown("""
<style>
    /* Cor de fundo principal */
    .stApp {
        background-color: #F0F2F6;
    }
    /* Estilo dos botões */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #1E88E5;
        color: #1E88E5;
        background-color: #FFFFFF;
    }
    .stButton>button:hover {
        border-color: #1565C0;
        color: #1565C0;
    }
    /* Estilo do container da métrica do timer */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }
    /* Título principal */
    h1 {
        color: #263238;
    }
    /* Títulos de secção */
    h2, h3 {
        color: #37474F;
    }
</style>
""", unsafe_allow_html=True)


# --- CONFIGURAÇÕES GLOBAIS E ESTADO DA SESSÃO ---
CURSOS = ["História do Brasil I", "História Moderna", "Metodologia da História"]
SEGMENTOS_PADRAO = [
    {"nome": "Aquecimento", "min": 10},
    {"nome": "Exposição", "min": 25},
    {"nome": "Atividade", "min": 20},
    {"nome": "Fechamento", "min": 5},
]

def inicializar_estado():
    """Inicializa o estado da sessão se ainda não existir."""
    if "rodando" not in st.session_state:
        st.session_state.rodando = False
    if "inicio_seg" not in st.session_state:
        st.session_state.inicio_seg = 0.0
    if "duracao_seg" not in st.session_state:
        st.session_state.duracao_seg = 0.0
    if "idx_seg" not in st.session_state:
        st.session_state.idx_seg = 0
    if "log" not in st.session_state:
        st.session_state.log = []
    if "presenca" not in st.session_state:
        st.session_state.presenca = {}
    if "segmentos" not in st.session_state:
        st.session_state.segmentos = SEGMENTOS_PADRAO

inicializar_estado()

def resetar_aula():
    """Reseta o estado do timer e do log para uma nova aula."""
    st.session_state.rodando = False
    st.session_state.inicio_seg = 0.0
    st.session_state.duracao_seg = 0.0
    st.session_state.idx_seg = 0
    st.session_state.log = []


# --- SIDEBAR (BARRA LATERAL) ---
with st.sidebar:
    st.header("👨‍🏫 Aula")
    curso = st.selectbox("Disciplina", CURSOS, index=0)
    data = st.date_input("Data", datetime.today())

    st.markdown("---")
    st.header("👥 Presença")
    nomes = st.text_area("Cole a lista de alunos (um por linha):", height=150, placeholder="Aluno 1\nAluno 2\nAluno 3")
    
    lista_nomes = [n.strip() for n in nomes.splitlines() if n.strip()]
    if lista_nomes:
        for n in lista_nomes:
            st.session_state.presenca.setdefault(n, False)
        
        for n in sorted(lista_nomes):
            st.session_state.presenca[n] = st.checkbox(n, value=st.session_state.presenca.get(n, False))

    st.markdown("---")
    if st.button("📥 Baixar Presença (CSV)"):
        if not st.session_state.presenca:
            st.warning("Nenhum aluno na lista para baixar.")
        else:
            dfp = pd.DataFrame(
                [{"data": data.isoformat(), "curso": curso, "nome": n, "presente": p}
                 for n, p in st.session_state.presenca.items()]
            )
            st.download_button(
                "Clique para baixar",
                dfp.to_csv(index=False).encode("utf-8"),
                file_name=f"presenca_{curso}_{data}.csv",
                mime="text/csv"
            )

# --- PAINEL PRINCIPAL ---
st.title("Painel do Dia de Aula")
st.caption("Timer por blocos, anotações rápidas e log automático da aula.")

col_timer, col_notas = st.columns([1.1, 1])

with col_timer:
    st.header("⏱️ Timer da Aula")

    # Configuração dos segmentos dentro de um expander
    with st.expander("⚙️ Configurar Blocos da Aula"):
        segs_editados = []
        for i, seg in enumerate(st.session_state.segmentos):
            col_a, col_b = st.columns([2, 1])
            nome = col_a.text_input(f"Nome do bloco {i+1}", seg["nome"], key=f"seg_nome_{i}")
            minutos = col_b.number_input("Minutos", 1, 180, seg["min"], key=f"seg_min_{i}")
            segs_editados.append({"nome": nome, "min": int(minutos)})
        st.session_state.segmentos = segs_editados

    # Informações do bloco atual
    idx_atual = st.session_state.idx_seg
    bloco_atual = st.session_state.segmentos[idx_atual]
    st.info(f"**Bloco atual:** {bloco_atual['nome']} — **Duração Prevista:** {bloco_atual['min']} min")

    # Controles do Timer
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    if col_t1.button("▶️ Iniciar/Retomar", disabled=st.session_state.rodando):
        st.session_state.rodando = True
        st.session_state.inicio_seg = time.time() - st.session_state.duracao_seg
        st.experimental_rerun()

    if col_t2.button("⏸️ Pausar", disabled=not st.session_state.rodando):
        st.session_state.rodando = False
        st.experimental_rerun()

    if col_t3.button("⏭️ Próximo Bloco"):
        gasto = st.session_state.duracao_seg / 60
        st.session_state.log.append({
            "data": data.isoformat(), "curso": curso,
            "bloco": bloco_atual["nome"], "min_previstos": bloco_atual["min"],
            "min_gastos": round(gasto, 1), "nota": "",
            "timestamp": datetime.now().isoformat()
        })
        # Avança para o próximo bloco
        st.session_state.idx_seg = min(idx_atual + 1, len(st.session_state.segmentos) - 1)
        st.session_state.rodando = False
        st.session_state.inicio_seg = 0.0
        st.session_state.duracao_seg = 0.0
        st.experimental_rerun()
    
    if col_t4.button("🔄 Resetar Aula"):
        resetar_aula()
        st.experimental_rerun()

    # Atualiza e exibe o tempo
    if st.session_state.rodando:
        st.session_state.duracao_seg = time.time() - st.session_state.inicio_seg

    decorrido = int(st.session_state.duracao_seg)
    restante = max(0, bloco_atual["min"] * 60 - decorrido)
    mm, ss = divmod(restante, 60)
    
    st.metric("Tempo Restante", f"{mm:02d}:{ss:02d}")
    
    # Barra de progresso visual
    progresso = min(1.0, decorrido / (bloco_atual["min"] * 60) if bloco_atual["min"] > 0 else 0)
    st.progress(progresso)

    # Auto-refresh enquanto o timer está rodando
    if st.session_state.rodando:
        time.sleep(1)
        st.experimental_rerun()

with col_notas:
    st.header("📝 Anotações e Log")

    # Área de anotações rápidas
    st.subheader("Brain Dump (Ideias/Notas)")
    nota = st.text_area("Escreva livremente durante a aula:", height=120, key="nota_solta")
    if st.button("➕ Adicionar Nota ao Log"):
        if nota:
            st.session_state.log.append({
                "data": data.isoformat(), "curso": curso, "bloco": "nota solta",
                "min_previstos": "", "min_gastos": "", "nota": nota,
                "timestamp": datetime.now().isoformat()
            })
            st.success("Nota adicionada ao log!")
            # Limpa o campo após adicionar
            st.session_state.nota_solta = "" 
            st.experimental_rerun()
        else:
            st.warning("Escreva algo na nota antes de adicionar.")

    # Área de tarefas
    st.subheader("✔️ Tarefas / Próximas Ações")
    todo = st.text_input("Ex.: Enviar e-mail para turma X", key="tarefa")
    if st.button("Registrar Tarefa"):
        if todo:
            st.session_state.log.append({
                "data": data.isoformat(), "curso": curso, "bloco": "tarefa",
                "min_previstos": "", "min_gastos": "", "nota": todo,
                "timestamp": datetime.now().isoformat()
            })
            st.success("Tarefa registrada no log!")
            st.session_state.tarefa = ""
            st.experimental_rerun()
        else:
            st.warning("Descreva a tarefa antes de registrar.")

# --- Visualização e Download do Log ---
st.markdown("---")
st.header("🧾 Log da Aula")

if st.session_state.log:
    dflog = pd.DataFrame(st.session_state.log)
    st.dataframe(dflog[['bloco', 'nota', 'min_previstos', 'min_gastos']])
    
    st.download_button(
        "📥 Baixar Log Completo (CSV)",
        dflog.to_csv(index=False).encode("utf-8"),
        file_name=f"log_{curso}_{data}.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhuma entrada no log ainda.")

