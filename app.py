# app.py
# -----------------------------------------------------------
# Calculos Uso do Solo - com abas, linha do tempo e waterfall
# Pré-requisitos (requirements.txt):
# streamlit>=1.33
# pandas>=2.2
# openpyxl>=3.1.2
# plotly>=5.22
# -----------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# Configuração da aplicação
# -----------------------------
st.set_page_config(
    page_title="Cálculos Uso do Solo",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# Helpers
# -----------------------------
def br(n, casas=4):
    """Formata número no padrão pt-BR com vírgula decimal."""
    if n is None:
        return "-"
    try:
        s = f"{float(n):,.{casas}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(n)

def to_num(serie):
    """Converte série para numérico com NaN->0 (seguro para somas)."""
    return pd.to_numeric(serie, errors="coerce").fillna(0)

def valida_colunas(df, colunas_esperadas):
    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    return faltantes

def parse_ids(texto):
    """Recebe '101, 102 ; 103' e devolve lista de strings normalizadas."""
    if not texto:
        return []
    separadores = [",", ";", "|", "\n"]
    for sep in separadores:
        texto = texto.replace(sep, ",")
    ids = [x.strip() for x in texto.split(",") if x.strip() != ""]
    return ids

# -----------------------------
# Título e instruções
# -----------------------------
st.title("📊 Cálculos Uso do Solo")
with st.sidebar:
    st.markdown("### Como usar")
    st.markdown(
        """
1. **Envie** a base em `.xlsx`.
2. **Informe** os IDs de *id. Matricula* separados por vírgula.
3. **Digite** a **Área Total** (use ponto como separador decimal).
4. Clique em **Recalcular** para ver:
   - **📋 Resumo** com somatórios
   - **🧭 Linha do tempo** dos cálculos com fórmulas
   - **📈 Waterfall** (cascata)
   - **📑 Dados filtrados**
        """
    )
    st.info("Dica: você pode colar os IDs direto do Excel; o app resolve vírgulas, ponto e vírgula e quebras de linha.")

# -----------------------------
# Upload do arquivo
# -----------------------------
arquivo = st.file_uploader("Envie sua base de dados (.xlsx)", type=["xlsx"], key="upload_arquivo")

# Nome da planilha (opcional)
sheet_name = None

if arquivo:
    try:
        # Carregamento inicial para identificar planilhas
        xl = pd.ExcelFile(arquivo, engine="openpyxl")
        if len(xl.sheet_names) > 1:
            sheet_name = st.selectbox("Selecione a planilha:", xl.sheet_names, index=0)
        else:
            sheet_name = xl.sheet_names[0]

        df = pd.read_excel(arquivo, sheet_name=sheet_name, engine="openpyxl")
        st.success("✅ Arquivo carregado com sucesso!")
        st.caption(f"Planilha utilizada: **{sheet_name}** — {df.shape[0]} linhas × {df.shape[1]} colunas")

    except Exception as e:
        st.error(f"Não foi possível ler o Excel: {e}")
        st.stop()
else:
    st.stop()

# -----------------------------
# Entradas
# -----------------------------
col_input1, col_input2 = st.columns([2, 1])
with col_input1:
    valor_h = st.text_input(
        "🔎 Digite os valores da coluna **'id. Matricula'** separados por vírgula",
        placeholder="ex.: 101, 102, 103"
    )
with col_input2:
    # Formulário para garantir o clique explícito
    with st.form("formulario_area_total", clear_on_submit=False):
        area_total_texto = st.text_input("✍️ Área Total", value="", help="Use ponto como separador decimal (ex.: 1234.5678)")
        recalcular = st.form_submit_button("🔄 Recalcular")

# -----------------------------
# Processamento
# -----------------------------
if not (valor_h and recalcular):
    st.stop()

# Validações de inputs
try:
    area_total_manual = round(float(area_total_texto), 4)
except ValueError:
    st.error("⚠️ Valor inválido de **Área Total**. Digite um número com **ponto** como separador decimal (ex: 1234.5678).")
    st.stop()

ids_matricula = parse_ids(valor_h)
if not ids_matricula:
    st.warning("⚠️ Informe ao menos **1** valor na coluna **'id. Matricula'**.")
    st.stop()

# Colunas esperadas na base
COL_ID = "id. Matricula"
COLS_REQUERIDAS = [
    COL_ID,
    "Área Plantada",
    "Área VEG",
    "Total APP",
    "Área RL (sem sobreposição da APP)",
    "Área Carreador",
    "Área Estrada",
    "Área INF",
]

faltantes = valida_colunas(df, COLS_REQUERIDAS)
if faltantes:
    st.error(
        "As seguintes colunas **não foram encontradas** na planilha selecionada:\n\n"
        + "\n".join([f"- `{c}`" for c in faltantes])
    )
    st.stop()

# Filtragem por IDs
df[COL_ID] = df[COL_ID].astype(str).str.strip()
filtrado = df[df[COL_ID].isin(ids_matricula)].copy()

if filtrado.empty:
    st.warning("⚠️ Nenhuma linha encontrada com os valores informados na coluna **'id. Matricula'**.")
    st.stop()

# Garantir numéricos
filtrado["Área Plantada"] = to_num(filtrado["Área Plantada"])
filtrado["Área VEG"] = to_num(filtrado["Área VEG"])
filtrado["Total APP"] = to_num(filtrado["Total APP"])
filtrado["Área RL (sem sobreposição da APP)"] = to_num(filtrado["Área RL (sem sobreposição da APP)"])
filtrado["Área Carreador"] = to_num(filtrado["Área Carreador"])
filtrado["Área Estrada"] = to_num(filtrado["Área Estrada"])
filtrado["Área INF"] = to_num(filtrado["Área INF"])

# Somas
soma_area_plantada = filtrado["Área Plantada"].sum()
soma_area_veg = filtrado["Área VEG"].sum()
soma_total_app = filtrado["Total APP"].sum()
soma_area_rl = filtrado["Área RL (sem sobreposição da APP)"].sum()
soma_area_carreador = filtrado["Área Carreador"].sum()
soma_area_estrada = filtrado["Área Estrada"].sum()
soma_area_inf = filtrado["Área INF"].sum()
area_benfeitoria = soma_area_carreador + soma_area_estrada + soma_area_inf

# Cálculos sequenciais
resultado_1 = area_total_manual - soma_area_plantada
resultado_2 = resultado_1 - soma_total_app
resultado_3 = resultado_2 - soma_area_rl
resultado_4 = resultado_3 - area_benfeitoria
resultado_final = resultado_4 - soma_area_veg

# Estrutura para timeline
passos = [
    {
        "passo": 1,
        "titulo": "Área Total (início)",
        "delta": area_total_manual,
        "acumulado": area_total_manual,
        "formula": f"{area_total_manual:.4f}"
    },
    {
        "passo": 2,
        "titulo": "Descontar Área Plantada",
        "delta": -soma_area_plantada,
        "acumulado": resultado_1,
        "formula": f"{area_total_manual:.4f} - {soma_area_plantada:.4f} = {resultado_1:.4f}"
    },
    {
        "passo": 3,
        "titulo": "Descontar APP",
        "delta": -soma_total_app,
        "acumulado": resultado_2,
        "formula": f"{resultado_1:.4f} - {soma_total_app:.4f} = {resultado_2:.4f}"
    },
    {
        "passo": 4,
        "titulo": "Descontar RL (sem sobreposição da APP)",
        "delta": -soma_area_rl,
        "acumulado": resultado_3,
        "formula": f"{resultado_2:.4f} - {soma_area_rl:.4f} = {resultado_3:.4f}"
    },
    {
        "passo": 5,
        "titulo": "Descontar Benfeitorias (Carreador + Estrada + INF)",
        "delta": -area_benfeitoria,
        "acumulado": resultado_4,
        "formula": f"{resultado_3:.4f} - {area_benfeitoria:.4f} = {resultado_4:.4f}"
    },
    {
        "passo": 6,
        "titulo": "Descontar Vegetação Nativa (VEG)",
        "delta": -soma_area_veg,
        "acumulado": resultado_final,
        "formula": f"{resultado_4:.4f} - {soma_area_veg:.4f} = {resultado_final:.4f}"
    },
]
df_passos = pd.DataFrame(passos)

# -----------------------------
# Abas
# -----------------------------
aba_resumo, aba_timeline, aba_waterfall, aba_dados = st.tabs(
    ["📋 Resumo", "🧭 Linha do tempo", "📈 Waterfall", "📑 Dados filtrados"]
)

# --------- 📋 Resumo ---------
with aba_resumo:
    st.subheader("📋 Dados Agregados")
    col1, col2, col3 = st.columns(3)
    col1.metric("Área Total (manual)", br(area_total_manual))
    col2.metric("Área Plantada (soma)", br(soma_area_plantada))
    col3.metric("Área VEG (soma)", br(soma_area_veg))

    col4, col5, col6 = st.columns(3)
    col4.metric("Total APP (soma)", br(soma_total_app))
    col5.metric("Área RL (sem APP) (soma)", br(soma_area_rl))
    col6.metric("Benfeitorias (soma)", br(area_benfeitoria), help="Carreador + Estrada + INF")

    st.subheader("📊 Resultado Final")
    st.metric(
        "Saldo após todos os descontos",
        br(resultado_final),
        help="Área Total - (Plantada + APP + RL sem APP + Benfeitorias + VEG)"
    )

# --------- 🧭 Linha do tempo ---------
with aba_timeline:
    st.subheader("🧭 Linha do tempo dos cálculos")

    # CSS simples para uma timeline vertical
    st.markdown("""
    <style>
    .timeline {position: relative; margin: 1rem 0 0 0; padding-left: 1.2rem;}
    .timeline:before {content:""; position:absolute; left:8px; top:0; bottom:0; width:2px; background:#4a90e2; opacity:.35;}
    .tl-item {position: relative; margin: 0 0 1.15rem 0; padding-left: .8rem;}
    .tl-item:before {content:""; position:absolute; left:-2px; top:.35rem; width:12px; height:12px; border-radius:50%;
                     background:#1f6feb; box-shadow:0 0 0 3px rgba(31,111,235,.18);}
    .tl-title {font-weight:600;}
    .tl-badge {display:inline-block; font-size:.78rem; background:#0e4429; color:#d2ffd6;
               padding:.1rem .45rem; border-radius:.4rem; margin-left:.3rem;}
    .tl-formula {color:#8b949e; font-family: ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","Courier New",monospace;}
    .tl-valor {font-variant-numeric: tabular-nums; font-weight:600;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for p in passos:
        tipo = "início" if p["passo"] == 1 else ("desconto" if p["delta"] < 0 else "ajuste")
        signo = "−" if p["delta"] < 0 else "+"
        st.markdown(f"""
        <div class="tl-item">
          <div class="tl-title">Passo {p['passo']}: {p['titulo']}
            <span class="tl-badge">{tipo}</span>
          </div>
          <div>Variação: <span class="tl-valor">{br(p['delta'])}</span> ({signo})</div>
          <div>Acumulado: <span class="tl-valor">{br(p['acumulado'])}</span></div>
          <div class="tl-formula">Fórmula: {p['formula']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.download_button(
        "⬇️ Baixar linha do tempo (CSV)",
        data=df_passos.to_csv(index=False).encode("utf-8"),
        file_name="linha_do_tempo_calculos.csv",
        mime="text/csv"
    )

# --------- 📈 Waterfall ---------
with aba_waterfall:
    st.subheader("📈 Visualização em cascata (Waterfall)")

    labels = [
        "Área Total (início)",
        "− Área Plantada",
        "− APP",
        "− RL (sem APP)",
        "− Benfeitorias",
        "− Vegetação Nativa",
        "Resultado Final"
    ]
    measures = ["relative", "relative", "relative", "relative", "relative", "relative", "total"]
    valores = [
        area_total_manual,
        -soma_area_plantada,
        -soma_total_app,
        -soma_area_rl,
        -area_benfeitoria,
        -soma_area_veg,
        resultado_final
    ]

    fig = go.Figure(go.Waterfall(
        measure=measures,
        x=labels,
        y=valores,
        text=[br(v) for v in valores],
        textposition="outside",
        connector={"line": {"color": "#9aa4b2"}},
        decreasing={"marker": {"color": "#e5534b"}},
        increasing={"marker": {"color": "#2da44e"}},
        totals={"marker": {"color": "#0969da"}}
    ))
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=420)
    st.plotly_chart(fig, use_container_width=True)

# --------- 📑 Dados filtrados ---------
with aba_dados:
    st.subheader("📑 Dados filtrados por ID")
    st.dataframe(filtrado, use_container_width=True)
    st.caption(f"{filtrado.shape[0]} linhas selecionadas para os IDs: {', '.join(ids_matricula)}")






