import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculos Uso do Solo", layout="wide")
st.title("📊 Calculos Uso do Solo")

# Upload do arquivo
arquivo = st.file_uploader("Envie sua base de dados (.xlsx)", type=["xlsx"], key="upload_arquivo")

if arquivo:
    df = pd.read_excel(arquivo, engine='openpyxl')
    st.success("✅ Arquivo carregado com sucesso!")

    # Entrada para múltiplos IDs
    valor_h = st.text_input("🔎 Digite os valores da coluna 'id. Matricula' separados por vírgula (ex: 101,102,103)")

    # Formulário para área total
    with st.form("formulario_area_total"):
        area_total_texto = st.text_input("✍️ Digite o valor da Área Total (use ponto como separador decimal)", value="")
        recalcular = st.form_submit_button("🔄 Recalcular")

    if valor_h and recalcular:
        try:
            area_total_manual = round(float(area_total_texto), 4)
        except ValueError:
            st.error("⚠️ Valor inválido. Digite um número com ponto como separador decimal (ex: 1234.5678).")
            st.stop()

        # Processar múltiplos IDs
        ids_matricula = [id.strip() for id in valor_h.split(",")]
        filtrado = df[df['id. Matricula'].astype(str).isin(ids_matricula)]

        if not filtrado.empty:
            # Somar os valores das colunas relevantes
            soma_area_plantada = filtrado['Área Plantada'].sum()
            soma_area_veg = filtrado['Área VEG'].sum()
            soma_total_app = filtrado['Total APP'].sum()
            soma_area_rl = filtrado['Área RL (sem sobreposição da APP)'].sum()
            soma_area_carreador = filtrado['Área Carreador'].sum()
            soma_area_estrada = filtrado['Área Estrada'].sum()
            soma_area_inf = filtrado['Área INF'].sum()
            area_benfeitoria = soma_area_carreador + soma_area_estrada + soma_area_inf

            # Realizar os cálculos sequenciais
            resultado_1 = area_total_manual - soma_area_plantada
            resultado_2 = resultado_1 - soma_total_app
            resultado_3 = resultado_2 - soma_area_rl
            resultado_4 = resultado_3 - area_benfeitoria
            resultado_final = resultado_4 - soma_area_veg

            # Exibir resultados
            st.subheader("📋 Dados Agregados")
            col1, col2, col3 = st.columns(3)
            col1.metric("Área Total (manual)", f"{area_total_manual:.4f}")
            col2.metric("Área Plantada (soma)", f"{soma_area_plantada:.4f}")
            col3.metric("Área VEG (soma)", f"{soma_area_veg:.4f}")

            col4, col5, col6 = st.columns(3)
            col4.metric("Total APP (soma)", f"{soma_total_app:.4f}")
            col5.metric("Área RL (sem APP) (soma)", f"{soma_area_rl:.4f}")
            col6.metric("Área Benfeitorias (soma)", f"{area_benfeitoria:.4f}", help="Área Carreador + Área Estrada + Área INF")

            st.subheader("📊 Cálculos Sequenciais")
            col7, col8 = st.columns(2)
            col7.metric("Descontado Plantio", f"{resultado_1:.4f}", help="Área Total - Área Plantada")
            col8.metric("Desconto APP", f"{resultado_2:.4f}", help="Descontado Plantio - Total APP")

            col9, col10 = st.columns(2)
            col9.metric("Desconto RL Sem sobreposição APP", f"{resultado_3:.4f}", help="Desconto APP - Área RL (sem APP)")
            col10.metric("Desconto Benfeitorias", f"{resultado_4:.4f}", help="Desconto RL Sem sobreposição APP - Área Benfeitorias")

            st.metric("Desconto Vegetacao Nativa", f"{resultado_final:.4f}", help="Desconto Benfeitorias - Área VEG")
        else:
            st.warning("⚠️ Nenhuma linha encontrada com os valores informados na coluna 'id. Matricula'.")





