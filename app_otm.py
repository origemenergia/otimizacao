import streamlit as st
import pandas as pd
import itertools
import math
import time

def formata_brl(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

def otimizar_fechamento(pocos_df, vazao_alvo, dias, max_combo=6, limitar=False, progresso=None):
    if limitar:
        pocos_df = pocos_df.nlargest(30, 'Vazão_m3_d')
        max_combo = 6

    registros = pocos_df.to_dict('records')

    melhor = None
    melhor_prejuizo = None

    total_combinacoes = sum(math.comb(len(registros), r) for r in range(1, min(max_combo, len(registros)) + 1))
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
            if progresso and atual % 100 == 0:
                progresso.progress(min(int((atual / total_combinacoes) * 100), 100))
    if progresso:
        progresso.progress(100)
    return melhor

st.title("🛠️ Otimizador de Fechamento de Poços")

uploaded_file = st.file_uploader("📄 Envie o arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = carregar_dados(uploaded_file)

    abas = st.tabs(["🔄 Otimização Automática", "🧮 Fechamento Manual"])

    # --- Aba Automática ---
    with abas[0]:
        campo = st.selectbox("🛢️ Campo", ['Pilar', 'Furado'])
        dias = st.number_input("📆 Dias de fechamento", min_value=1, step=1, value=1)
        vazao_alvo = st.number_input("🌊 Vazão alvo diária (m³/d)", min_value=0.1, value=100.0)

        excluir_poços_checkbox = st.checkbox("🚫 Indicar poços que NÃO devem ser fechados")
        poços_disponiveis = df[(df['Campo'].str.lower() == campo.lower()) & (df['Vazão_m3_d'] > 0)].nlargest(30, 'Vazão_m3_d')['Poço'].tolist()
        poços_excluir = []
        if excluir_poços_checkbox:
            poços_excluir = st.multiselect("Selecione os poços", poços_disponiveis)

        definir_max = st.checkbox("🔢 Definir máximo de poços para fechamento", value=False)

        if definir_max:
            max_combo = st.slider("Máximo de poços por combinação", 1, 10, 3)
            max_combos_a_testar = [max_combo]
        else:
            max_combos_a_testar = list(range(1, 7))  # testar de 1 a 6

        df_sel = df[(df['Campo'].str.lower() == campo.lower()) & (df['Vazão_m3_d'] > 0)]
        df_sel = df_sel.nlargest(30, 'Vazão_m3_d')

        if poços_excluir:
            df_sel = df_sel[~df_sel['Poço'].isin(poços_excluir)]

        if st.button("🚀 Executar Otimização"):
            st.write("⏳ Processando...")
            inicio = time.time()
            progresso = st.progress(0)  # barra única criada aqui

            melhor_resultado = None
            melhor_prejuizo = None
            for max_c in max_combos_a_testar:
                resultado = otimizar_fechamento(df_sel, vazao_alvo, dias, max_combo=max_c, limitar=False, progresso=progresso)
                if resultado and (melhor_prejuizo is None or resultado['Prejuízo USD'] < melhor_prejuizo):
                    melhor_prejuizo = resultado['Prejuízo USD']
                    melhor_resultado = resultado

            fim = time.time()
            st.write(f"⏱️ Tempo de execução: {fim - inicio:.2f} s")

            if melhor_resultado:
                st.subheader("✅ Melhor Resultado:")
                st.write(f"**Poços a fechar:** {', '.join(melhor_resultado['Poços a Fechar'])}")
                st.write(f"**Fluxo fechado:** {formata_brl(melhor_resultado['Fluxo Fechado (m³/d)'])} (m³/d)")
                st.write(f"**Prejuízo total:** {formata_brl(melhor_resultado['Prejuízo USD'])} (USD)")
            else:
                st.warning("⚠️ Nenhuma combinação atende aos critérios.")

    # --- Aba Manual ---
    with abas[1]:
        campo_m = st.selectbox("🛢️ Campo", ['Pilar', 'Furado'], key="campo_manual")
        df_m = df[(df['Campo'].str.lower() == campo_m.lower()) & (df['Vazão_m3_d'] > 0)]
        df_m = df_m.nlargest(30, 'Vazão_m3_d')

        pocos_disponiveis = df_m['Poço'].tolist()
        pocos_selecionados = st.multiselect("🛠️ Selecione os poços que deseja fechar manualmente", pocos_disponiveis)

        dias_fechamento = st.number_input("📆 Dias de fechamento para todos os poços selecionados", min_value=1, step=1, value=1)

        excluir_manual = st.checkbox("🚫 Indicar os poços que NÃO devem ser fechados")

        poços_excluir_manual = []
        if excluir_manual:
            poços_excluir_manual = st.multiselect("Selecione os poços", pocos_disponiveis)

        if st.button("📊 Calcular fechamento manual"):
            df_selecionados = df_m[df_m['Poço'].isin(pocos_selecionados)]
            fluxo_total = df_selecionados['Vazão_m3_d'].sum()
            preju_total = df_selecionados['Lucro_USD_d'].sum() * dias_fechamento

            st.subheader("📌 Resultado Manual:")
            st.write(f"**Fluxo fechado:** {formata_brl(fluxo_total)} (m³/d)")
            st.write(f"**Prejuízo total:** {formata_brl(preju_total)} (USD)")

            # Filtra poços excluídos para otimização
            df_para_otimizacao = df_m
            if poços_excluir_manual:
                df_para_otimizacao = df_para_otimizacao[~df_para_otimizacao['Poço'].isin(poços_excluir_manual)]

            # Comparação com otimização automática limitada para agilizar
            st.subheader("📊 Comparação com Otimização:")

            resultado_teste = otimizar_fechamento(df_para_otimizacao, fluxo_total, dias_fechamento, limitar=True)

            if resultado_teste:
                dif = preju_total - resultado_teste['Prejuízo USD']
                st.write(f"💡 Com a estratégia otimizada, você economizaria **{formata_brl(dif)} (USD)**.")
                st.write(f"**Poços otimizados:** {', '.join(resultado_teste['Poços a Fechar'])}")
                st.write(f"**Prejuízo otimizado:** {formata_brl(resultado_teste['Prejuízo USD'])} (USD)")
                st.write(f"**Fluxo fechado (otimizado):** {formata_brl(resultado_teste['Fluxo Fechado (m³/d)'])} (m³/d)")
            else:
                st.warning("⚠️ Nenhuma combinação otimizada encontrada para a mesma meta de fluxo.")
