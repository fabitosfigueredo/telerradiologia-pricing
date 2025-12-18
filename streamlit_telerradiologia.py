"""
App Streamlit – Assistente de Coleta Telerradiologia (Comercial → Pricing)

Objetivo:
- Guiar o Comercial na coleta de informações
- Evitar respostas técnicas (JSON)
- Gerar automaticamente o TEXTO DO PEDIDO DE PRICING

Execução:
streamlit run streamlit_telerradiologia.py

Pré-requisitos:
- pip install streamlit
- ollama rodando com modelo mistral (opcional, não usado diretamente aqui)
"""

import streamlit as st
import json

# ==========================
# FUNÇÃO: GERAR TEXTO DE PRICING
# ==========================

def gerar_texto_pricing(data: dict) -> str:
    linhas = []

    linhas.append("Pedido de Precificação – Telerradiologia\n")
    linhas.append(
        "Solicita-se a elaboração de proposta de precificação para prestação de serviços de telerradiologia, conforme escopo abaixo:\n"
    )

    # Modalidades
    modalidades = ", ".join(data["modalidades"])
    linhas.append(f"Modalidades contempladas:\n{modalidades}\n")

    # Volumetria
    linhas.append("Volumetria estimada:")
    for mod, v in data["volumetria"].items():
        linhas.append(
            f"- {mod}: volume médio mensal de {v['volume_mensal']} exames "
            f"({v['urgente']}% urgentes, {v['internado']}% internados, {v['eletivo']}% eletivos)"
        )
    linhas.append("")

    # Abrangência
    linhas.append(
        f"Abrangência do contrato:\nAtendimento em {data['quantidade_unidades']} unidade(s).\n"
    )

    # Infraestrutura
    linhas.append("Infraestrutura:")
    linhas.append(f"- Link de envio das imagens: {data['link_envio']}")
    linhas.append(f"- Armazenamento das imagens: {data['armazenamento']}")
    linhas.append(f"- Integração de sistemas: {data['integracao']}")
    linhas.append(f"- PACS do cliente: {data['pacs']}")
    linhas.append(f"- HIS do cliente: {data['his']}")
    linhas.append(f"- Servidor PACS / Router: {data['servidor_pacs']}")
    linhas.append(f"- Portal do Paciente: {data['portal_paciente']}\n")

    # Modelo comercial
    linhas.append("Modelo comercial:")
    linhas.append(f"- Modelo de remuneração: {data['modelo_remuneracao']}")
    linhas.append(f"- Volume mínimo mensal: {data['volume_minimo']}\n")

    # SLA
    linhas.append("SLA de laudos:")
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
        "quantidade_unidades": None,
        "link_envio": None,
        "armazenamento": None,
        "integracao": None,
        "pacs": None,
        "his": None,
        "servidor_pacs": None,
        "portal_paciente": None,
        "modelo_remuneracao": None,
        "volume_minimo": None,
        "sla": {}
    }

# ==========================
# UI
# ==========================

st.title("Assistente de Precificação – Telerradiologia")

# ==========================
# FLUXO
# ==========================

if st.session_state.etapa == "modalidades":
    st.subheader("1. Modalidades")

    modalidades = st.multiselect(
        "Quais modalidades fazem parte do escopo?",
        ["Raios-X", "Tomografia Computadorizada", "Ressonância Magnética ", "Mamografia", "Densitometria", "Medicina Nuclear"]
    )

    if st.button("Próximo") and modalidades:
        st.session_state.data["modalidades"] = modalidades
        st.session_state.etapa = "volumetria"
        st.rerun()

elif st.session_state.etapa == "volumetria":
    st.subheader("2. Volumetria por modalidade")

    for mod in st.session_state.data["modalidades"]:
        with st.expander(f"{mod}"):
            volume = st.number_input(
                f"Volume mensal – {mod}", min_value=0, step=1, key=f"vol_{mod}"
            )
            urgente = st.number_input(
                f"% Urgente – {mod}", min_value=0, max_value=100, step=1, key=f"urg_{mod}"
            )
            internado = st.number_input(
                f"% Internado – {mod}", min_value=0, max_value=100, step=1, key=f"int_{mod}"
            )

            eletivo = 100 - urgente - internado
            st.caption(f"% Eletivo calculado automaticamente: {eletivo}%")

            if eletivo < 0:
                st.error("Percentuais inválidos (soma maior que 100)")
            else:
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
    st.subheader("3. Abrangência")

    qtd = st.number_input("Quantidade de unidades atendidas", min_value=1, step=1)

    if st.button("Próximo"):
        st.session_state.data["quantidade_unidades"] = qtd
        st.session_state.etapa = "infra"
        st.rerun()

elif st.session_state.etapa == "infra":
    st.subheader("4. Infraestrutura e Integração")

    st.session_state.data["link_envio"] = st.selectbox(
        "Link de envio das imagens", ["FIDI", "Cliente"]
    )
    st.session_state.data["armazenamento"] = st.selectbox(
        "Armazenamento das imagens", ["FIDI", "Cliente"]
    )
    st.session_state.data["integracao"] = st.selectbox(
        "Necessita integração de sistemas?", ["Sim", "Não"]
    )
    st.session_state.data["pacs"] = st.text_input("PACS do cliente")
    st.session_state.data["his"] = st.text_input("HIS do cliente")
    st.session_state.data["servidor_pacs"] = st.selectbox(
        "Servidor PACS / Router", ["FIDI", "Cliente"]
    )
    st.session_state.data["portal_paciente"] = st.selectbox(
        "Portal do Paciente", ["Sim", "Não"]
    )

    if st.button("Próximo"):
        st.session_state.etapa = "financeiro"
        st.rerun()

elif st.session_state.etapa == "financeiro":
    st.subheader("5. Modelo Comercial")

    st.session_state.data["modelo_remuneracao"] = st.selectbox(
        "Modelo de remuneração",
        ["Por exame", "Pacote mensal", "Escalonado por volume", "Misto"]
    )

    st.session_state.data["volume_minimo"] = st.selectbox(
        "Existe volume mínimo mensal?", ["Sim", "Não"]
    )

    if st.button("Próximo"):
        st.session_state.etapa = "sla"
        st.rerun()

elif st.session_state.etapa == "sla":
    st.subheader("6. SLA de Laudos")

    urgente = st.text_input("SLA – Urgentes", value="1h")
    internado = st.text_input("SLA – Internados", value="12h")
    eletivo = st.text_input("SLA – Eletivos", value="48h")

    if st.button("Finalizar"):
        st.session_state.data["sla"] = {
            "urgente": urgente,
            "internado": internado,
            "eletivo": eletivo
        }
        st.session_state.etapa = "final"
        st.rerun()

elif st.session_state.etapa == "final":
    st.success("Coleta finalizada com sucesso")

    texto_pricing = gerar_texto_pricing(st.session_state.data)

    st.subheader("Texto do pedido de pricing")
    st.text_area(
        "Copie e cole este texto no e-mail ou sistema interno:",
        texto_pricing,
        height=420
    )

    with st.expander("Ver dados estruturados (uso interno)"):
        st.json(st.session_state.data)
