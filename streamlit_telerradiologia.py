"""
App Streamlit – Assistente de Coleta Telerradiologia (Comercial → Pricing)

Objetivo:
- Guiar o Comercial na coleta de informações
- Evitar respostas técnicas (JSON)
- Permitir VOLTAR para revisar informações
- Gerar automaticamente o TEXTO DO PEDIDO DE PRICING

Execução:
streamlit run streamlit_telerradiologia.py

Pré-requisitos:
- pip install streamlit
"""

import streamlit as st
import json

# ==========================
# MAPA DE NAVEGAÇÃO
# ==========================

ETAPA_ANTERIOR = {
    "volumetria": "modalidades",
    "quantidade_unidades": "volumetria",
    "infra": "quantidade_unidades",
    "financeiro": "infra",
    "sla": "financeiro",
    "final": "sla",
}

def botao_voltar(etapa_atual):
    etapa_anterior = ETAPA_ANTERIOR.get(etapa_atual)
    if etapa_anterior and st.button("⬅ Voltar"):
        st.session_state.etapa = etapa_anterior
        st.rerun()

# ==========================
# TEXTO DE PRICING
# ==========================

def gerar_texto_pricing(data: dict) -> str:
    linhas = []

    linhas.append("Pedido de Precificação – Telerradiologia\n")
    linhas.append("Solicita-se a elaboração de proposta de precificação para prestação de serviços de telerradiologia, conforme escopo abaixo:\n")

    linhas.append("Modalidades contempladas:")
    linhas.append(", ".join(data["modalidades"]) + "\n")

    linhas.append("Volumetria estimada:")
    for mod, v in data["volumetria"].items():
        linhas.append(
            f"- {mod}: {v['volume_mensal']} exames/mês "
            f"({v['urgente']}% urgentes, {v['internado']}% internados, {v['eletivo']}% eletivos)"
        )
    linhas.append("")

    if data["modelo_remuneracao"] == "Por exame":
        linhas.append("Histórico – Volumetria média mensal (últimos 6 meses):")
        for mod, v in data.get("volumetria_6m", {}).items():
            linhas.append(f"- {mod}: {v} exames/mês")
        linhas.append("")

    linhas.append(f"Abrangência: {data['quantidade_unidades']} unidade(s).\n")

    linhas.append("Infraestrutura:")
    linhas.append(f"- Link de envio: {data['link_envio']}")
    linhas.append(f"- Armazenamento: {data['armazenamento']}")
    linhas.append(f"- Integração: {data['integracao']}")
    linhas.append(f"- PACS: {data['pacs']}")
    linhas.append(f"- HIS: {data['his']}")
    linhas.append(f"- Servidor PACS: {data['servidor_pacs']}")
    linhas.append(f"- Portal do Paciente: {data['portal_paciente']}")

    if "Mamografia" in data["modalidades"]:
        linhas.append(f"- Preenchimento MS (Mamografia): {data['siscan']}")

    linhas.append("\nModelo comercial:")
    linhas.append(f"- Remuneração: {data['modelo_remuneracao']}\n")

    linhas.append("SLA:")
    linhas.append(f"- Urgentes: {data['sla']['urgente']}")
    linhas.append(f"- Internados: {data['sla']['internado']}")
    linhas.append(f"- Eletivos: {data['sla']['eletivo']}\n")

    linhas.append("Favor considerar as premissas acima para elaboração do pricing.")

    return "\n".join(linhas)

# ==========================
# ESTADO INICIAL
# ==========================

if "etapa" not in st.session_state:
    st.session_state.etapa = "modalidades"

if "data" not in st.session_state:
    st.session_state.data = {
        "modalidades": [],
        "volumetria": {},
        "volumetria_6m": {},
        "quantidade_unidades": None,
        "link_envio": None,
        "armazenamento": None,
        "integracao": None,
        "pacs": None,
        "his": None,
        "servidor_pacs": None,
        "portal_paciente": None,
        "modelo_remuneracao": None,
        "siscan": None,
        "sla": {}
    }

st.title("Assistente de Precificação – Telerradiologia")

# ==========================
# FLUXO
# ==========================

if st.session_state.etapa == "modalidades":
    st.subheader("1. Modalidades")

    modalidades = st.multiselect(
        "Selecione as modalidades:",
        ["Raios-X", "Tomografia", "Ressonância Magnética", "Mamografia", "Densitometria", "Ultrassonografia"],
        default=st.session_state.data["modalidades"],
    )

    if st.button("Próximo") and modalidades:
        st.session_state.data["modalidades"] = modalidades
        st.session_state.etapa = "volumetria"
        st.rerun()

elif st.session_state.etapa == "volumetria":
    botao_voltar("volumetria")
    st.subheader("2. Volumetria estimada")

    for mod in st.session_state.data["modalidades"]:
        with st.expander(mod, expanded=True):
            volume = st.number_input(f"Volume mensal – {mod}", min_value=0, step=1, key=f"vol_{mod}")
            urgente = st.number_input(f"% Urgente – {mod}", 0, 100, key=f"urg_{mod}")
            internado = st.number_input(f"% Internado – {mod}", 0, 100, key=f"int_{mod}")

            eletivo = 100 - urgente - internado
            st.caption(f"Eletivo calculado: {eletivo}%")

            st.session_state.data["volumetria"][mod] = {
                "volume_mensal": volume,
                "urgente": urgente,
                "internado": internado,
                "eletivo": eletivo
            }

    if st.button("Próximo"):
        st.session_state.etapa = "quantidade_unidades"
        st.rerun()

elif st.session_state.etapa == "quantidade_unidades":
    botao_voltar("quantidade_unidades")
    st.subheader("3. Abrangência")

    qtd = st.number_input("Quantidade de unidades", min_value=1, step=1)

    if st.button("Próximo"):
        st.session_state.data["quantidade_unidades"] = qtd
        st.session_state.etapa = "infra"
        st.rerun()

elif st.session_state.etapa == "infra":
    botao_voltar("infra")
    st.subheader("4. Infraestrutura")

    st.session_state.data["link_envio"] = st.selectbox("Link de envio das imagens", ["FIDI", "Cliente"])
    st.session_state.data["armazenamento"] = st.selectbox("Armazenamento das imagens", ["FIDI", "Cliente"])
    st.session_state.data["integracao"] = st.selectbox("Integração entre sistemas", ["Sim", "Não"])
    st.session_state.data["pacs"] = st.text_input("PACS do cliente")
    st.session_state.data["his"] = st.text_input("HIS/Prontuáro eletrônico do Paciente")
    st.session_state.data["servidor_pacs"] = st.selectbox("Servidor PACS/Desktop Router", ["FIDI", "Cliente"])
    st.session_state.data["portal_paciente"] = st.selectbox("Portal do Paciente", ["Sim", "Não"])

    if "Mamografia" in st.session_state.data["modalidades"]:
        st.session_state.data["siscan"] = st.selectbox(
            "Preenchimento de sistema do Ministério da Saúde (Mamografia)",
            ["SISCAN", "SISMAMA", "Nenhum dos dois"]
        )

    if st.button("Próximo"):
        st.session_state.etapa = "financeiro"
        st.rerun()

elif st.session_state.etapa == "financeiro":
    botao_voltar("financeiro")
    st.subheader("5. Modelo Comercial")

    st.session_state.data["modelo_remuneracao"] = st.selectbox(
        "Modelo de remuneração",
        ["Por exame", "Fixo + Variável"]
    )

    if st.session_state.data["modelo_remuneracao"] == "Por exame":
        st.markdown("### Volumetria média mensal – últimos 6 meses")
        for mod in st.session_state.data["modalidades"]:
            st.session_state.data["volumetria_6m"][mod] = st.number_input(
                f"{mod} – média mensal (6 meses)",
                min_value=0,
                step=1,
                key=f"hist_{mod}"
            )

    if st.button("Próximo"):
        st.session_state.etapa = "sla"
        st.rerun()

elif st.session_state.etapa == "sla":
    botao_voltar("sla")
    st.subheader("6. SLA")

    st.session_state.data["sla"] = {
        "urgente": st.text_input("Urgente", "1h"),
        "internado": st.text_input("Internado", "12h"),
        "eletivo": st.text_input("Eletivo", "48h")
    }

    if st.button("Finalizar"):
        st.session_state.etapa = "final"
        st.rerun()

elif st.session_state.etapa == "final":
    botao_voltar("final")
    st.success("Coleta finalizada")

    texto = gerar_texto_pricing(st.session_state.data)
    st.text_area("Texto do pedido de pricing", texto, height=450)

    with st.expander("Dados estruturados"):
        st.json(st.session_state.data)
