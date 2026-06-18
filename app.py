import streamlit as st
from simulacao import simulacao_completa

st.set_page_config(
    page_title="Simulador OuLab",
    layout="wide"
)

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    st.image("logo.png", width=120)

with col_titulo:
    st.title("Simulador OuLab")

st.header("Parâmetros")

col1, col2 = st.columns(2)

with col1:

    prob_cliente_normal_recrutar = st.number_input(
        "Prob. Cliente Comum Recrutar Alguém",
        value=0.03,
        step=0.01
    )

    prob_retencao = st.number_input(
        "Prob. Retenção Cliente Comum",
        value=0.80,
        step=0.01
    )

    prob_bom_recrutador = st.number_input(
        "Prob. Bom Recrutador",
        value=0.20,
        step=0.01
    )

    prob_bom_recrutador_filho = st.number_input(
        "Prob. Filho de Bom Recrutador também ser",
        value=0.30,
        step=0.01
    )

    prob_venda_prime = st.number_input(
        "Prob. de um Cliente Prime comprar no mês de 1 consultor",
        value=0.08,
        step=0.01
    )

with col2:
    
    meses_simulacao = st.number_input(
        "Meses de Simulação",
        min_value=1,
        max_value=60,
        value=60
    )

    valor_final = st.number_input(
        "Consultores Ativos no Último Mês (em milhares)",
        min_value=1,
        max_value=60,
        value=80
    )

    forma_de_evolucao = st.selectbox(
        "Forma de Evolução de Volume de Consultores",
        ["linear", "logaritmica"]
    )

status = st.empty()

def atualizar_status(texto):
    status.info(texto)


if st.button("Executar Simulação"):

    with st.spinner("Processando..."):

        df_mensal, tb_total, tb_bonus = simulacao_completa(
            prob_cliente_normal_recrutar=prob_cliente_normal_recrutar,
            prob_retencao=prob_retencao,
            prob_bom_recrutador=prob_bom_recrutador,
            prob_bom_recrutador_filho=prob_bom_recrutador_filho,
            prob_venda_prime=prob_venda_prime,
            meses_simulacao=meses_simulacao,
            valor_final=valor_final,
            forma_de_evolucao=forma_de_evolucao,
            tipo_analise='último mes',
            callback_status=atualizar_status
        )

    st.success("Simulação concluída!")

    aba1, aba2, aba3 = st.tabs([
        "Mensal",
        "Total (Receita em Milhões)",
        "Bônus"
    ])

    with aba1:
        st.dataframe(df_mensal.style.format(precision=2, decimal=",", thousands="."),
            use_container_width=True)

    with aba2:
        st.dataframe(tb_total.style.format(precision=2, decimal=",", thousands="."),
            use_container_width=True)

    with aba3:
        st.dataframe(tb_bonus.style.format(precision=2, decimal=",", thousands="."),
            use_container_width=True)