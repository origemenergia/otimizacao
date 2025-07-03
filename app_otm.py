import streamlit as st
import pandas as pd
import itertools
import math
import time

@st.cache_data
def carregar_dados(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df = df.rename(columns={
        'POÇO': 'Poço',
        'Campo': 'Campo',
        'Vazão Água (m³/dia)': 'Vazão_m3_d',
        'Lucratividade (USD/d)': 'Lucro_USD_d'
    })
    return df

def otimizar_fechamento(pocos_df, vazao_alvo, dias, max_combo):
    registros = pocos_df.to_dict('records')
    melhor = None
    melhor_prejuizo = None

    total_combinacoes = sum(math.comb(len(registros), r) for r in range(1, min(max_combo, len(registros)) + 1))

    progresso = st.progress(0)
    atual = 0

    for r in range(1, min(max_combo, len(registros)) + 1):
        combos = itertools.combinations(registros, r)
        for combo in combos:
            atual += 1
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
            # Atualiza a barra a cada 100 iterações para não travar
            if atual % 100 == 0:
                progresso.progress(min(int((atual / total_combinacoes) * 100), 100))

    progresso.progress(100)
    return melhor

st.title("🔧 Otimização de Fechamento de Poços")

uploaded_file = st.file_uploader("📄 Envie o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = carregar_dados(uploaded_file)

    campo = st.selectbox("🛢️ Campo", ['Pilar', 'Furado'])
    dias = st.number_input("📆 Dias de fechamento", min_value=1, step=1, value=3)
    vazao_alvo = st.number_input("🌊 Vazão alvo diária (m³/d)", min_value=0.1)
    max_combo = st.slider("🔢 Máximo de poços por combinação", 1, 10, 3)

    if campo.lower() == 'pilar':
        df_sel = df[df['Campo'].str.lower() == 'pilar']
    else:
        df_sel = df[df['Campo'].str.lower() != 'pilar']
    df_sel = df_sel[df_sel['Vazão_m3_d'] > 0]

    if st.button("🚀 Executar Otimização"):
        st.write("⏳ Processando...")
        inicio = time.time()
        resultado = otimizar_fechamento(df_sel, vazao_alvo, dias, max_combo)
        fim = time.time()
        st.write(f"⏱️ Tempo de execução: {fim - inicio:.2f} s")

        if resultado:
            st.subheader("✅ Resultado:")
            st.write(f"**Poços a fechar:** {', '.join(resultado['Poços a Fechar'])}")
            st.write(f"**Fluxo fechado:** {resultado['Fluxo Fechado (m³/d)']:.2f}")
            st.write(f"**Prejuízo total (USD):** {resultado['Prejuízo USD']:.2f}")
        else:
            st.warning("⚠️ Nenhuma combinação atende aos critérios.")
