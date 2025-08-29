# app.py
# -----------------------------------------------------------
# Cálculos Uso do Solo - com ponto de COMPLETUDE dinâmico
# Abas: Resumo | Linha do tempo | Waterfall | Dados filtrados
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
    separadores = [",", ";", "|", "\n", "\t"]
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
   - **🧭 Linha do tempo** com fórmulas e **ponto de completude**
   - **📈 Waterfall** destacando onde o saldo zera
   - **📑 Dados filtrados**
        """
    )
    st.info("Dica: você pode colar os IDs direto do Excel; o app entende vírgula, ponto e vírgula e quebra de linha.")

# -----------------------------
# Upload do arquivo
# -----------------------------
arquivo = st.file_uploader("Envie sua base de dados (.xlsx)", type=["xlsx"], key="upload_arquivo")

if arquivo:
    try:
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
    with st.form("formulario_area_total", clear_on_submit=False):
        area_total_texto = st.text_input("✍️ Área Total", value="", help="Use ponto como separador decimal (ex.: 1234.5678)")
        recalcular = st.form_submit_button("🔄 Recalcular")

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

# -----------------------------
# Validação de colunas e filtro
# -----------------------------
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

df[COL_ID] = df[COL_ID].astype(str).str.strip()
filtrado = df[df[COL_ID].isin(ids_matricula)].copy()

if filtrado.empty:
    st.warning("⚠️ Nenhuma linha encontrada com os valores informados na coluna **'id. Matricula'**.")
    st.stop()

# Garantir numéricos
for c in ["Área Plantada", "Área VEG", "Total APP",
          "Área RL (sem sobreposição da APP)", "Área Carreador", "Área Estrada", "Área INF"]:
    filtrado[c] = to_num(filtrado[c])

# -----------------------------
# Somas e cálculos base
# -----------------------------
soma_area_plantada = filtrado["Área Plantada"].sum()
soma_area_veg = filtrado["Área VEG"].sum()
soma_total_app = filtrado["Total APP"].sum()
soma_area_rl = filtrado["Área RL (sem sobreposição da APP)"].sum()
soma_area_carreador = filtrado["Área Carreador"].sum()
soma_area_estrada = filtrado["Área Estrada"].sum()
soma_area_inf = filtrado["Área INF"].sum()
area_benfeitoria = soma_area_carreador + soma_area_estrada + soma_area_inf

# Sequência das categorias (ordem dos descontos)
categorias = [
    ("Área Plantada", soma_area_plantada, "Plantada"),
    ("APP", soma_total_app, "APP"),
    ("RL (sem sobreposição da APP)", soma_area_rl, "RL"),
    ("Benfeitorias (Carreador + Estrada + INF)", area_benfeitoria, "Benfeitorias"),
    ("Vegetação Nativa (VEG)", soma_area_veg, "VEG"),
]

# -----------------------------
# Construção dinâmica da TIMELINE e do WATERFALL
# com ponto de COMPLETUDE (saldo = 0)
# -----------------------------
passos = []            # para timeline e CSV
labels_wf = []         # labels waterfall
vals_wf = []           # valores waterfall
measures_wf = []       # 'relative' ou 'total'
completude_encontrada = False
etapa_completude_nome = None
faltante_para_completar = None
indice_wf_completude = None

# Passo inicial: saldo parte de Área Total
saldo = area_total_manual
passos.append({
    "passo": 1,
    "titulo": "Área Total (início)",
    "delta": area_total_manual,
    "acumulado": area_total_manual,
    "badge": "início",
    "formula": f"{area_total_manual:.4f}"
})
labels_wf.append("Área Total (início)")
vals_wf.append(area_total_manual)
measures_wf.append("relative")

passo_n = 1

for nome_completo, valor_cat, nome_curto in categorias:
    if saldo > 0:
        # Precisamos dessa quantidade para zerar
        precisa = saldo
        if valor_cat >= precisa and not completude_encontrada:
            # Esta categoria é onde o saldo zera
            # 1) Parte "até completar"
            passo_n += 1
            passos.append({
                "passo": passo_n,
                "titulo": f"{nome_completo} (até completar)",
                "delta": -precisa,
                "acumulado": 0.0,
                "badge": "completude",
                "formula": f"{saldo:.4f} - {precisa:.4f} = 0.0000"
            })
            labels_wf.append(f"{nome_curto} (até completar)")
            vals_wf.append(-precisa)
            measures_wf.append("relative")

            completude_encontrada = True
            etapa_completude_nome = nome_curto
            faltante_para_completar = precisa
            indice_wf_completude = len(labels_wf) - 1
            saldo = 0.0

            # 2) Se sobrar excedente dessa categoria, subtrair depois de zerar
            excedente = valor_cat - precisa
            if excedente > 0:
                passo_n += 1
                saldo -= excedente
                passos.append({
                    "passo": passo_n,
                    "titulo": f"{nome_completo} (excedente)",
                    "delta": -excedente,
                    "acumulado": saldo,
                    "badge": "excedente",
                    "formula": f"0.0000 - {excedente:.4f} = {saldo:.4f}"
                })
                labels_wf.append(f"{nome_curto} (excedente)")
                vals_wf.append(-excedente)
                measures_wf.append("relative")
        else:
            # Categoria inteira antes da completude
            passo_n += 1
            saldo -= valor_cat
            passos.append({
                "passo": passo_n,
                "titulo": f"Descontar {nome_completo}",
                "delta": -valor_cat,
                "acumulado": saldo,
                "badge": "desconto",
                "formula": f"{(saldo + valor_cat):.4f} - {valor_cat:.4f} = {saldo:.4f}"
            })
            labels_wf.append(f"− {nome_curto}")
            vals_wf.append(-valor_cat)
            measures_wf.append("relative")
    else:
        # Já passou do zero: tudo vira excedente
        passo_n += 1
        saldo -= valor_cat
        passos.append({
            "passo": passo_n,
            "titulo": f"Descontar {nome_completo}",
            "delta": -valor_cat,
            "acumulado": saldo,
            "badge": "desconto",
            "formula": f"{(saldo + valor_cat):.4f} - {valor_cat:.4f} = {saldo:.4f}"
        })
        labels_wf.append(f"− {nome_curto}")
        vals_wf.append(-valor_cat)
        measures_wf.append("relative")

# Resultado final (total)
passo_n += 1
passos.append({
    "passo": passo_n,
    "titulo": "Resultado Final",
    "delta": saldo,  # apenas informativo na timeline
    "acumulado": saldo,
    "badge": "total",
    "formula": f"Saldo final = {saldo:.4f}"
})
labels_wf.append("Resultado Final")
vals_wf.append(saldo)
measures_wf.append("total")

df_passos = pd.DataFrame(passos)

# -----------------------------
# Abas
# -----------------------------
aba_resumo, aba_timeline, aba_waterfall, aba_dados = st.tabs(
    ["📋 Resumo", "🧭 Linha do tempo", "📈 Waterfall", "📑 Dados filtrados"]
)

# --------- 📋 Resumo ---------
with aba_resumo:
    # Somatórios brutos
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
        br(saldo),
        help="Área Total - (Plantada + APP + RL sem APP + Benfeitorias + VEG; considerando completude no meio da categoria quando necessário)"
    )

    # Mensagens de completude
    total_deducao = soma_area_plantada + soma_total_app + soma_area_rl + area_benfeitoria + soma_area_veg
    if not completude_encontrada and total_deducao < area_total_manual:
        st.info(
            f"⚠️ As deduções **não** alcançam a Área Total. Ainda faltam **{br(area_total_manual - total_deducao)}** para completar."
        )
    elif completude_encontrada:
        st.success(
            f"✅ Ciclo de **completude** ocorre em **{etapa_completude_nome}**, "
            f"consumindo **{br(faltante_para_completar)}** dessa categoria para zerar o saldo (0). "
            f"Qualquer valor remanescente aparece como **excedente** nas etapas seguintes."
        )
    else:
        st.success("✅ As deduções fecham **exatamente** a Área Total (sem excedente).")

# --------- 🧭 Linha do tempo ---------
with aba_timeline:
    st.subheader("🧭 Linha do tempo dos cálculos (completude destacada)")

    # CSS para timeline
    st.markdown("""
    <style>
    .timeline {position: relative; margin: 1rem 0 0 0; padding-left: 1.2rem;}
    .timeline:before {content:""; position:absolute; left:8px; top:0; bottom:0; width:2px; background:#4a90e2; opacity:.35;}
    .tl-item {position: relative; margin: 0 0 1.15rem 0; padding-left: .8rem;}
    .tl-item:before {content:""; position:absolute; left:-2px; top:.35rem; width:12px; height:12px; border-radius:50%;
                     background:#1f6feb; box-shadow:0 0 0 3px rgba(31,111,235,.18);}
    .tl-title {font-weight:600;}
    .tl-badge {display:inline-block; font-size:.78rem; background:#57606a; color:#fff;
               padding:.1rem .45rem; border-radius:.4rem; margin-left:.3rem;}
    .tl-badge.inicio {background:#6e7781;}
    .tl-badge.desconto {background:#0e4429; color:#d2ffd6;}
    .tl-badge.excedente {background:#6e7781; color:#fff;}
    .tl-badge.completude {background:#1a7f37; color:#eaffea;}
    .tl-badge.total {background:#0969da; color:#fff;}
    .tl-formula {color:#8b949e; font-family: ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono","Courier New",monospace;}
    .tl-valor {font-variant-numeric: tabular-nums; font-weight:600;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="timeline">', unsafe_allow_html=True)
    for p in passos:
        badge_class = {
            "início": "inicio",
            "desconto": "desconto",
            "excedente": "excedente",
            "completude": "completude",
            "total": "total"
        }.get(p["badge"], "desconto")
        signo = "−" if p["delta"] < 0 else "+"
        st.markdown(f"""
        <div class="tl-item">
          <div class="tl-title">Passo {p['passo']}: {p['titulo']}
            <span class="tl-badge {badge_class}">{p['badge']}</span>
          </div>
          <div>Valor da Área: <span class="tl-valor">{br(p['delta'])}</span> ({signo})</div>
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
    st.subheader("📈 Visualização em cascata (Waterfall) — com completude")

    fig = go.Figure(go.Waterfall(
        measure=measures_wf,
        x=labels_wf,
        y=vals_wf,
        text=[br(v) for v in vals_wf],
        textposition="outside",
        connector={"line": {"color": "#9aa4b2"}},
        decreasing={"marker": {"color": "#e5534b"}},  # descontos (negativos)
        increasing={"marker": {"color": "#2da44e"}},  # aumentos (não usados aqui)
        totals={"marker": {"color": "#0969da"}}       # total final
    ))
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=460)

    # Anotação do ponto de completude (= saldo 0)
    if completude_encontrada and indice_wf_completude is not None:
        fig.add_hline(y=0, line_color="#1a7f37", line_width=2, opacity=0.6)
        fig.add_annotation(
            x=labels_wf[indice_wf_completude],
            y=0,
            text="Completude (saldo 0)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#1a7f37",
            font=dict(color="#1a7f37", size=12),
            ay=-40
        )

    st.plotly_chart(fig, use_container_width=True)

# --------- 📑 Dados filtrados ---------
with aba_dados:
    st.subheader("📑 Dados filtrados por ID")
    st.dataframe(filtrado, use_container_width=True)
    st.caption(f"{filtrado.shape[0]} linhas selecionadas para os IDs: {', '.join(ids_matricula)}")

