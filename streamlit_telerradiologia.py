"""
App Streamlit – Assistente de Coleta Telerradiologia (Comercial → Pricing)
VERSÃO v3 – UX + Validações + Endereço + Financeiro corrigido
"""

import streamlit as st
import requests

# ==========================
# UTIL – CEP (ViaCEP)
# ==========================

def buscar_cep(cep):
    cep = cep.replace("-", "").strip()
    if len(cep) != 8:
        return None
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("erro"):
            return None
        return data
    except Exception:
        return None

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

    if data.get("endereco_unidade"):
        e = data["endereco_unidade"]
        linhas.append(
            f"- Endereço da unidade: {e['logradouro']}, {e['bairro']} – "
            f"{e['cidade_uf']} (CEP {e['cep']})"
        )

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
        "sla": {},
        "endereco_unidade": None
    }

# ==========================
# HEADER + PROGRESSO
# ==========================

st.title("Assistente de Precificação – Telerradiologia")
st.progress((ETAPAS.index(st.session_state.etapa) + 1) / len(ETAPAS))

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

    erro_us = False

    for mod in st.session_state.data["modalidades"]:
        with st.expander(mod, expanded=True):

            st.markdown("**Volumetria mensal**")
            volume = st.number_input(
                f"Volume mensal estimado – {mod}",
                min_value=0,
                step=1,
                key=f"vol_{mod}"
            )

            if mod == "Ultrassonografia":
                doppler = st.number_input("% Doppler", 0, 100, key="us_doppler")
                fetal = st.number_input("% Fetal", 0, 100, key="us_fetal")
                soma = doppler + fetal
                simples = 100 - soma

                if soma > 100:
                    st.error("A soma de Doppler + Fetal não pode exceder 100%.")
                    erro_us = True

                horario = st.text_input("Horário de funcionamento *", placeholder="Ex: 07h às 19h")
                if not horario:
                    st.error("Horário obrigatório.")
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
                eletivo = 100 - (urgente + internado)

                st.session_state.data["volumetria"][mod] = {
                    "volume_mensal": volume,
                    "urgente": urgente,
                    "internado": internado,
                    "eletivo": eletivo
                }

    if st.button("Próximo"):
        if erro_us:
            st.error("Corrija os erros antes de avançar.")
        else:
            st.session_state.etapa = "quantidade_unidades"
            st.rerun()

# -------- UNIDADES --------
elif st.session_state.etapa == "quantidade_unidades":
    botao_voltar("quantidade_unidades")
    qtd = st.number_input("Quantidade de unidades", min_value=1, step=1)

    if st.button("Próximo"):
        st.session_state.data["quantidade_unidades"] = qtd
        st.session_state.etapa = "infra"
        st.rerun()

# -------- INFRA --------
elif st.session_state.etapa == "infra":
    botao_voltar("infra")
    st.subheader("4. Infraestrutura")

    erro_endereco = False

    st.session_state.data["link_envio"] = st.selectbox("Link de envio", ["Cliente", "FIDI"])
    st.session_state.data["armazenamento"] = st.selectbox("Armazenamento", ["Cliente", "FIDI"])
    st.session_state.data["servidor_pacs"] = st.selectbox("Desktop / Router", ["Cliente", "FIDI"])

    st.session_state.data["integracao"] = st.selectbox("Integração", ["Sim", "Não"])
    st.session_state.data["pacs"] = st.text_input("PACS")
    st.session_state.data["his"] = st.text_input("HIS")
    st.session_state.data["portal_paciente"] = st.selectbox("Portal do Paciente", ["Sim", "Não"])

    if st.session_state.data["link_envio"] == "FIDI":
        st.markdown("### Endereço da unidade (para estimativa do link)")

        cep = st.text_input("CEP *", placeholder="Ex: 01310-100")
        dados = buscar_cep(cep) if cep else None

        if cep and not dados:
            st.error("CEP inválido.")
            erro_endereco = True

        if dados:
            logradouro = st.text_input("Logradouro", dados["logradouro"])
            bairro = st.text_input("Bairro", dados["bairro"])
            cidade_uf = st.text_input("Cidade / UF", f"{dados['localidade']} / {dados['uf']}")

            st.session_state.data["endereco_unidade"] = {
                "cep": cep,
                "logradouro": logradouro,
                "bairro": bairro,
                "cidade_uf": cidade_uf
            }
        else:
            erro_endereco = True

    if st.button("Próximo"):
        if st.session_state.data["link_envio"] == "FIDI" and erro_endereco:
            st.error("Informe um endereço válido para avançar.")
        else:
            st.session_state.etapa = "financeiro"
            st.rerun()

# -------- FINANCEIRO (CORRIGIDO) --------
elif st.session_state.etapa == "financeiro":
    botao_voltar("financeiro")
    st.subheader("5. Modelo Comercial")

    st.session_state.data["modelo_remuneracao"] = st.selectbox(
        "Modelo de remuneração",
        ["Fixo + Variável", "Por exame"],
        index=0
    )

    if st.session_state.data["modelo_remuneracao"] == "Por exame":
        st.warning(
            "Informe a **média mensal** de exames (não a soma dos 6 meses).\n\n"
            "Essa informação é usada para **cálculo de breakeven**."
        )

        for mod in st.session_state.data["modalidades"]:
            st.session_state.data["volumetria_6m"][mod] = st.number_input(
                f"{mod} – média mensal (últimos 6 meses)",
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
    st.success("Coleta finalizada.")

    texto = gerar_texto_pricing(st.session_state.data)
    st.text_area("Texto do pedido de pricing", texto, height=450)
