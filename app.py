import streamlit as st
import pandas as pd
import matplotlib
import seaborn as sns
import plotly.express as px

# Configura o estilo dark para o Streamlit e para Plotly
sns.set_theme(style="dark")
plt_style = "dark_background"

# Definindo a stake: 1 unit = STAKE_VALOR reais
STAKE_VALOR = 1000.0

def main():
    st.set_page_config(layout="wide")

    # CSS para centralizar os dados na tabela e ajustar a largura
    st.markdown("""
    <style>
    [data-testid="stDataFrame"] div[data-testid="cell"] {
        justify-content: center;
        text-align: center;
    }
    [data-testid="stDataFrame"] table {
        table-layout: auto !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ------------------------------------------------
    # 1) Seletor de planilhas
    # ------------------------------------------------
    sheet_options = ["CSCorito_Abril", "CSCorito_Maio"]
    sheet_name = st.selectbox("Escolha o mês:", sheet_options)
    mes = sheet_name.split("_")[-1]
    st.title(f"Relatório CSCorito - Mês {mes}")

    # ID da planilha e URL de acesso
    sheet_id = "1u0CPINUTdbYaL4tzsZ-wYWVgGO2Rq3zJkRsR5dpVvAU"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    # ------------------------------------------------
    # 2) Ler e processar os dados do Google Sheets
    # ------------------------------------------------
    df = pd.read_csv(url)
    df.drop_duplicates(inplace=True)

    # Converter "DATA" para datetime (assumindo que a coluna se chame "DATA")
    df["Data"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")
    # Converter "PROFIT" para float (substituindo vírgula por ponto)
    df["PROFIT"] = df["PROFIT"].astype(str).str.replace(",", ".", regex=False)
    df["PROFIT"] = pd.to_numeric(df["PROFIT"], errors="coerce")
    # Criar a coluna "Units" (equivalente ao profit)
    df["Units"] = df["PROFIT"]
    # Remover colunas que não serão exibidas
    for col in ["DATA", "PROFIT", "REALIZADA?"]:
        if col in df.columns:
            df.drop(col, axis=1, inplace=True)

    # ------------------------------------------------
    # 3) Exibir a Tabela Completa (Paginada)
    # ------------------------------------------------
    st.subheader("Entradas")
    page_size = 20
    # Para a exibição da tabela, ordenamos de forma descrescente (entradas mais recentes primeiro)
    df_table = df.sort_values(by="Data", ascending=False)
    total_rows = len(df_table)
    total_pages = max((total_rows + page_size - 1) // page_size, 1)

    if total_rows == 0:
        st.write("Não há registros para exibir.")
        return

    page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_page = df_table.iloc[start_idx:end_idx].copy()

    # Reordenar as colunas para que "Data" seja a primeira
    desired_cols = ["Data", "HR", "CONFRONTO", "Método", "Units"]
    existing_cols = [c for c in desired_cols if c in df_page.columns]
    remaining_cols = [c for c in df_page.columns if c not in existing_cols]
    df_page = df_page[existing_cols + remaining_cols]
    df_page.reset_index(drop=True, inplace=True)

    st.dataframe(df_page, use_container_width=True)
    st.write(f"Exibindo linhas {start_idx + 1} até {min(end_idx, total_rows)} de {total_rows}.")

    # ------------------------------------------------
    # 4) Dados para Gráficos: Ordenar os dados em ordem cronológica (ascendente)
    # ------------------------------------------------
    df_graph = df.sort_values(by="Data", ascending=True).copy()
    df_daily = df_graph.groupby(df_graph["Data"].dt.date)["Units"].sum().reset_index()
    df_daily.columns = ["Data", "Units_Diaria"]
    df_daily = df_daily.sort_values("Data")
    df_daily["Acumulado"] = df_daily["Units_Diaria"].cumsum()
    df_daily["Acumulado_Reais"] = df_daily["Acumulado"] * STAKE_VALOR

    # ------------------------------------------------
    # 5) Valor Atual do Mês (em Units e Reais)
    # Exibe antes dos gráficos, com fonte de 16px.
    # ------------------------------------------------
    df_graph["AnoMes"] = df_graph["Data"].dt.to_period("M").astype(str)
    df_monthly = df_graph.groupby("AnoMes")["Units"].sum().reset_index()
    df_monthly.columns = ["AnoMes", "Units_Mensais"]
    df_monthly = df_monthly.sort_values("AnoMes")
    ultimo_mes = df_monthly["AnoMes"].max() if not df_monthly.empty else None
    if ultimo_mes:
        dados_ultimo_mes = df_monthly.loc[df_monthly["AnoMes"] == ultimo_mes].iloc[0]
        units_ultimo_mes = dados_ultimo_mes["Units_Mensais"]
        reais_ultimo_mes = units_ultimo_mes * STAKE_VALOR
        st.markdown(
            f"<p style='font-size:16px;'>No mês {ultimo_mes}, você está com {units_ultimo_mes:.2f} unidades (R$ {reais_ultimo_mes:,.2f}).</p>",
            unsafe_allow_html=True
        )
    else:
        st.write("Não há dados mensais para exibir.")

    # ------------------------------------------------
    # 6) Gráficos Interativos com Plotly Express
    # ------------------------------------------------
    # Gráfico para Evolução Acumulada em Units
    fig_units = px.line(
        df_daily,
        x="Data",
        y="Acumulado",
        title="Evolução do Profit (Acumulado Diário) - Unidades",
        markers=True,
        template="plotly_dark"
    )
    fig_units.update_traces(line=dict(color="#39FF14", width=2), marker=dict(size=8, color="#39FF14"))
    fig_units.update_layout(
        xaxis_title="Data",
        yaxis_title="Unidades Acumuladas",
        title_font_size=14,
        font_color="white",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_units, use_container_width=True)

    # Gráfico para Evolução Acumulada em Reais
    fig_reais = px.line(
        df_daily,
        x="Data",
        y="Acumulado_Reais",
        title="Evolução do Profit (Acumulado Diário) em R$",
        markers=True,
        template="plotly_dark"
    )
    fig_reais.update_traces(line=dict(color="#39FF14", width=2), marker=dict(size=8, color="#39FF14"))
    fig_reais.update_layout(
        xaxis_title="Data",
        yaxis_title="Reais (R$)",
        title_font_size=14,
        font_color="white",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig_reais, use_container_width=True)

if __name__ == "__main__":
    main()
