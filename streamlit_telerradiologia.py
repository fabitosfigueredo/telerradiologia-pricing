"""
App Streamlit – Assistente de Coleta Telerradiologia (Comercial → Pricing)
VERSÃO v3 – UX + Validações

Execução:
streamlit run streamlit_telerradiologia_v3_ux_validado.py
"""

import streamlit as st

# ==========================
# CONFIG UX GLOBAL
# ==========================

ETAPAS = ["modalidades", "volumetria", "quantidade_unidades", "infra", "financeiro", "sla", "final"]

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
    linhas.append(
        "Solicita-se a elaboração de proposta de precificação para prestação "
        "de serviços de telerradiologia, conforme escopo abaixo:\n"
    )

    linhas.append("Modalidades contempladas:")
    linhas.append(", ".join(data["modalidades"]) + "\n")

    linhas.append("Volumetria estimada:")
    for mod, v in data["volumetria"].items():
        if mod == "Ultrassonografia":
            linhas.append(
                f"- Ultrassonografia: {v['volume_mensal']} exames/mês "
                f"({v['doppler']}% Doppler, {v['fetal']}% Fetal, {v['simples']}% Simples)"
            )
            linhas.append(f"  Horário de funcionamento: {v['horario_funcionamento']}")
        else:
            linhas.append(
                f"- {mod}: {v['volume_mensal']} exames/mês "
                f"({v['urgente']}% urgentes, {v['internado']}% internados, {v['eletivo']}% eletivos)"
            )
    linhas.append("")

    if data["modelo_remuneracao"] == "Por exame":
        linhas.append("Histórico – média mensal (últimos 6 meses):")
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
    linhas.append(f"- Desktop / Router: {data['servidor_pacs']}")
    linhas.append(f"- Portal do Paciente: {data['portal_paciente']}")

    if "Mamografia" in data["modalidades"]:
        linhas.append(f"- Preenchimento MS (Mamografia): {data['siscan']}")

    linhas.append("\nModelo comercial:")
    linhas.append(f"- Remuneração: {data['modelo_remuneracao']}\n")

    linhas.append("SLA (em horas):")
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
        "modelo_remuneracao": "Fixo + Variável",
        "siscan": None,
        "sla": {}
    }

# ==========================
# HEADER + PROGRESSO
# ==========================

st.title("Assistente de Precificação – Telerradiologia")

indice = ETAPAS.index(st.session_state.etapa) + 1
st.progress(indice / len(ETAPAS))

# ==========================
# SIDEBAR – RESUMO
# ==========================

with st.sidebar:
    st.markdown("## 📋 Resumo")
    st.write("**Modalidades:**", ", ".join(st.session_state.data["modalidades"]) or "-")
    st.write("**Unidades:**", st.session_state.data["quantidade_unidades"] or "-")
    st.write("**Modelo:**", st.session_state.data["modelo_remuneracao"] or "-")

    if st.session_state.data["sla"]:
        st.markdown("**SLA (em horas)**")
        st.caption(
            f"Urgente: {st.session_state.data['sla']['urgente']}h | "
            f"Internado: {st.session_state.data['sla']['internado']}h | "
            f"Eletivo: {st.session_state.data['sla']['eletivo']}h"
        )

# ==========================
# FLUXO
# ==========================

# -------- MODALIDADES --------
if st.session_state.etapa == "modalidades":
    st.subheader("1. Modalidades")
    st.caption("Selecione apenas as modalidades que farão parte do contrato.")

    modalidades = st.multiselect(
        "Modalidades",
        [
            "Raios-X",
            "Tomografia",
            "Ressonância Magnética",
            "Mamografia",
            "Densitometria",
            "Ultrassonografia"
        ],
        default=st.session_state.data["modalidades"]
    )

    if st.button("Próximo") and modalidades:
        st.session_state.data["modalidades"] = modalidades
        st.session_state.etapa = "volumetria"
        st.rerun()

# -------- VOLUMETRIA --------
elif st.session_state.etapa == "volumetria":
    botao_voltar("volumetria")
    st.subheader("2. Volumetria estimada")
    st.caption("Informe volumes médios mensais.")

    erro_us = False

    for mod in st.session_state.data["modalidades"]:
        with st.expander(mod, expanded=True):

            volume = st.number_input(
                "Volume mensal estimado",
                min_value=0,
                step=1,
                key=f"vol_{mod}"
            )

            if mod == "Ultrassonografia":
                st.info("Perfis diferentes impactam custo (Doppler e Fetal).")

                doppler = st.number_input("% Doppler", 0, 100, key="us_doppler")
                fetal = st.number_input("% Fetal", 0, 100, key="us_fetal")

                soma = doppler + fetal
                simples = 100 - soma

                if soma > 100:
                    st.error("A soma de Doppler + Fetal não pode exceder 100%.")
                    erro_us = True
                else:
                    st.caption(f"Simples calculado automaticamente: {simples}%")

                horario = st.text_input(
                    "Horário de funcionamento *",
                    placeholder="Ex: 07h às 19h"
                )

                if not horario:
                    st.error("O horário de funcionamento da Ultrassonografia é obrigatório.")
                    erro_us = True

                st.session_state.data["volumetria"][mod] = {
                    "volume_mensal": volume,
                    "doppler": doppler,
                    "fetal": fetal,
                    "simples": simples,
                    "horario_funcionamento": horario
                }

            else:
                urgente = st.number_input("% Urgente", 0, 100, key=f"urg_{mod}")
                internado = st.number_input("% Internado", 0, 100, key=f"int_{mod}")

                soma = urgente + internado
                eletivo = 100 - soma

                if soma > 100:
                    st.error("A soma de Urgente + Internado não pode exceder 100%.")
                else:
                    st.caption(f"Eletivo calculado automaticamente: {eletivo}%")

                st.session_state.data["volumetria"][mod] = {
                    "volume_mensal": volume,
                    "urgente": urgente,
                    "internado": internado,
                    "eletivo": eletivo
                }

    if st.button("Próximo"):
        if erro_us:
            st.error("Corrija os erros da Ultrassonografia antes de avançar.")
        else:
            st.session_state.etapa = "quantidade_unidades"
            st.rerun()

# -------- UNIDADES --------
elif st.session_state.etapa == "quantidade_unidades":
    botao_voltar("quantidade_unidades")
    st.subheader("3. Abrangência")

    qtd = st.number_input(
        "Quantidade de unidades atendidas",
        min_value=1,
        step=1,
        value=st.session_state.data["quantidade_unidades"] or 1
    )

    if st.button("Próximo"):
        st.session_state.data["quantidade_unidades"] = qtd
        st.session_state.etapa = "infra"
        st.rerun()

# -------- INFRA --------
elif st.session_state.etapa == "infra":
    botao_voltar("infra")
    st.subheader("4. Infraestrutura")

    with st.expander("Responsabilidades", expanded=True):
        st.session_state.data["link_envio"] = st.selectbox("Link de envio", ["Cliente", "FIDI"])
        st.session_state.data["armazenamento"] = st.selectbox("Armazenamento", ["Cliente", "FIDI"])
        st.session_state.data["servidor_pacs"] = st.selectbox("Desktop / Router", ["Cliente", "FIDI"])

    with st.expander("Sistemas", expanded=True):
        st.session_state.data["integracao"] = st.selectbox("Integração entre sistemas", ["Sim", "Não"])
        st.session_state.data["pacs"] = st.text_input("PACS", placeholder="Ex: MV, Pixeon, Tasy")
        st.session_state.data["his"] = st.text_input("HIS", placeholder="Ex: MV Soul, Tasy")
        st.session_state.data["portal_paciente"] = st.selectbox("Portal do Paciente", ["Sim", "Não"])

    if "Mamografia" in st.session_state.data["modalidades"]:
        st.session_state.data["siscan"] = st.selectbox(
            "Sistema MS (Mamografia)",
            ["SISCAN", "SISMAMA", "Nenhum"]
        )

    if st.button("Próximo"):
        st.session_state.etapa = "financeiro"
        st.rerun()

# -------- FINANCEIRO --------
elif st.session_state.etapa == "financeiro":
    botao_voltar("financeiro")
    st.subheader("5. Modelo Comercial")

    st.session_state.data["modelo_remuneracao"] = st.selectbox(
        "Modelo de remuneração",
        ["Fixo + Variável", "Por exame"]
    )

    if st.session_state.data["modelo_remuneracao"] == "Por exame":
        st.warning(
            "Informe a **média mensal** de exames (não a soma dos 6 meses).\n\n"
            "Essa informação é usada para **cálculo de breakeven**."
        )

        for mod in st.session_state.data["modalidades"]:
            st.session_state.data["volumetria_6m"][mod] = st.number_input(
                f"{mod} – média mensal",
                min_value=0,
                step=1,
                key=f"hist_{mod}"
            )

    if st.button("Próximo"):
        st.session_state.etapa = "sla"
        st.rerun()

# -------- SLA --------
elif st.session_state.etapa == "sla":
    botao_voltar("sla")
    st.subheader("6. SLA em horas")
    st.caption("SLAs mais agressivos impactam custo e escala médica.")

    urgente = st.text_input("Urgente", placeholder="Ex: 2")
    internado = st.text_input("Internado", placeholder="Ex: 8")
    eletivo = st.text_input("Eletivo", placeholder="Ex: 48")

    if st.button("Finalizar"):
        if not urgente or not internado or not eletivo:
            st.error("Todos os campos de SLA são obrigatórios.")
        else:
            st.session_state.data["sla"] = {
                "urgente": urgente,
                "internado": internado,
                "eletivo": eletivo
            }
            st.session_state.etapa = "final"
            st.rerun()

# -------- FINAL --------
elif st.session_state.etapa == "final":
    botao_voltar("final")
    st.success("Coleta finalizada. Texto gerado abaixo.")

    texto = gerar_texto_pricing(st.session_state.data)

    st.text_area(
        "Texto do pedido de pricing (copie e cole)",
        texto,
        height=450
    )

    with st.expander("Dados estruturados (interno)"):
        st.json(st.session_state.data)
