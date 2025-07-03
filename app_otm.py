import streamlit as st
import pandas as pd
import itertools

# --- Configurações ---
ARQUIVO = r"C:\Users\adlehr.oliveira\Documents\database_valores_aleatorios.xlsx"
MAX_COMBO_PADRAO = 3

st.set_page_config(page_title="Fechamento de Poços", layout="centered")

st.title("🔧 Otimização de Fechamento de Poços")

# Função principal de otimização
def otimizar_fechamento(pocos_df, vazao_alvo, dias, max_combo):
    registros = pocos_df.to_dict('records')
    melhor = None
    melhor_prejuizo = None

    for r in range(1, min(max_combo, len(registros)) + 1):
        for combo in itertools.combinations(registros, r):
            soma_fluxo = sum(p['Vazão_m3_d'] for p in combo)
            if soma_fluxo >= vazao_alvo:
                preju = sum(p['Lucro_USD_d'] for p in combo) * dias
                if melhor_prejuizo is None or preju < melhor_prejuizo:
                    melhor_prejuizo = preju
                    melhor = {
                        'Poços a Fechar': [p['Poço'] for p in combo],
                        'Fluxo Fechado (m³/d)': soma_fluxo,
                        'Prejuízo USD': preju
                    }
    return melhor

# Leitura e preparação dos dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel(ARQUIVO)
    df = df.rename(columns={
        'POÇO': 'Poço',
        'Campo': 'Campo',
        'Vazão Água (m³/dia)': 'Vazão_m3_d',
        'Lucratividade (USD/d)': 'Lucro_USD_d'
    })
    return df

# Interface
df = carregar_dados()

campo = st.selectbox("Selecione o campo:", ['Pilar', 'Furado']).lower()
dias = st.number_input("Número de dias de fechamento:", min_value=1, value=5)
vazao_alvo = st.number_input("Vazão alvo total (m³/d):", min_value=0.0, step=10.0)
max_pocos = st.number_input("Máximo de poços a combinar:", min_value=1, value=MAX_COMBO_PADRAO)

# Filtrar poços do campo escolhido
df_sel = df.copy()
if campo == 'pilar':
    df_sel = df_sel[df_sel['Campo'] == 'Pilar']
else:
    df_sel = df_sel[df_sel['Campo'] != 'Pilar']

df_sel = df_sel[df_sel['Vazão_m3_d'] > 0]

# 🔒 Multiselect para proteger poços
todos_os_pocos = df_sel['Poço'].tolist()
protegidos = st.multiselect("Poços que não devem ser fechados:", todos_os_pocos)

# Remover poços protegidos do dataframe de otimização
df_otimizacao = df_sel[~df_sel['Poço'].isin(protegidos)]

# Botão de execução
if st.button("Executar Otimização"):

    with st.spinner("Otimizando..."):
        resultado = otimizar_fechamento(df_otimizacao, vazao_alvo, dias, max_pocos)

    if resultado:
        st.success("✅ Otimização concluída!")
        st.markdown(f"**Campo:** `{campo.title()}`")
        st.markdown(f"**Dias de fechamento:** `{dias}`")
        st.markdown(f"**Vazão alvo:** `{vazao_alvo} m³/d`")
        st.markdown(f"**Poços a fechar:** `{', '.join(resultado['Poços a Fechar'])}`")
        st.markdown(f"**Fluxo fechado:** `{resultado['Fluxo Fechado (m³/d)']:.2f} m³/d`")
        st.markdown(f"**Prejuízo total:** `${resultado['Prejuízo USD']:.2f}`")
    else:
        st.warning("⚠️ Nenhuma combinação de poços atinge a vazão alvo com os parâmetros informados.")
