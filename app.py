

import pandas as pd
import streamlit as st

from src.fila_prioridade import FilaPrioridade
from src.metricas import Metricas
from src.nivel import NivelManchester
from src.repositorio_log import RepositorioLog
from src.servico_atendimento import ServicoAtendimento
from src.simulador import GeradorPacientes, RelogioSimulado

st.set_page_config(page_title="Fila de Prioridade Hospitalar", page_icon="🏥", layout="wide")

CORES_LINHA = {
    "Vermelho": "#fecaca",
    "Laranja": "#fed7aa",
    "Amarelo": "#fef08a",
    "Verde": "#bbf7d0",
    "Azul": "#bfdbfe",
}


# ----------------------------------------------------------------------
# Estado da simulação (guardado entre os cliques)
# ----------------------------------------------------------------------
def iniciar_simulacao():
    repositorio = RepositorioLog("hospital.db")
    repositorio.limpar()
    st.session_state.repositorio = repositorio
    st.session_state.relogio = RelogioSimulado()
    st.session_state.gerador = GeradorPacientes()
    st.session_state.servico = ServicoAtendimento(FilaPrioridade(), repositorio)
    st.session_state.ultimo_chamado = None
    st.session_state.mensagem = None


if "servico" not in st.session_state:
    iniciar_simulacao()

servico = st.session_state.servico
relogio = st.session_state.relogio
repositorio = st.session_state.repositorio
agora = relogio.agora()


def opcao_nivel(nivel):
    return f"{nivel.numero} - {nivel.cor} ({nivel.descricao})"


OPCOES_NIVEL = {opcao_nivel(n): n.numero for n in NivelManchester}


def mostrar_mensagem():
    mensagem = st.session_state.mensagem
    if mensagem:
        tipo, texto = mensagem
        getattr(st, tipo)(texto)
        st.session_state.mensagem = None


# ----------------------------------------------------------------------
# Barra lateral: relógio e simulação (RN15)
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("Simulação")
    st.metric("Horário simulado", agora.strftime("%d/%m/%Y %H:%M"))
    st.caption("O relógio só anda quando você manda avançar.")

    coluna1, coluna2, coluna3 = st.columns(3)
    for coluna, minutos in ((coluna1, 15), (coluna2, 30), (coluna3, 60)):
        if coluna.button(f"+{minutos} min", key=f"avancar_{minutos}", width="stretch"):
            relogio.avancar(minutos)
            st.rerun()

    minutos_livres = st.number_input("Avançar (minutos)", min_value=1, max_value=1440, value=120, step=10)
    if st.button("Avançar tempo", width="stretch"):
        relogio.avancar(minutos_livres)
        st.rerun()

    st.divider()
    quantidade = st.number_input("Pacientes para gerar", min_value=1, max_value=500, value=20, step=5)
    if st.button("Gerar pacientes (teste de estresse)", width="stretch"):
        gerados = st.session_state.gerador.gerar(int(quantidade))
        for dados in gerados:
            servico.cadastrar_e_triar(
                dados["nome"], dados["id"], dados["nivel"], dados["enfermeiro"], relogio.agora()
            )
        st.session_state.mensagem = ("success", f"{len(gerados)} pacientes gerados e colocados na fila.")
        st.rerun()

    st.divider()
    if st.button("Reiniciar simulação", width="stretch"):
        iniciar_simulacao()
        st.rerun()

# ----------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------
st.title("🏥 Fila de Prioridade em Emergência Hospitalar")
st.caption("Protocolo de Manchester · aging contra starvation · alertas de SLA · auditoria em SQL")
mostrar_mensagem()

alertas = servico.alertas_sla(agora)
resumo1, resumo2, resumo3 = st.columns(3)
resumo1.metric("Pacientes na fila", servico.tamanho_fila())
resumo2.metric("Alertas de SLA", len(alertas))
resumo3.metric("Atendimentos concluídos", len(servico.listar_historico()))

aba_cadastro, aba_fila, aba_atendimento, aba_historico, aba_metricas, aba_sql = st.tabs([
    "Cadastro e triagem", "Fila ao vivo", "Atendimento", "Histórico", "Métricas", "Auditoria SQL",
])

# ----------------------------------------------------------------------
# Cadastro e triagem (RN01, RN02)
# ----------------------------------------------------------------------
with aba_cadastro:
    st.subheader("Cadastro do paciente e triagem")
    st.caption("O enfermeiro classifica o paciente no Protocolo de Manchester. O sistema registra quem classificou.")

    with st.form("form_cadastro", clear_on_submit=True):
        coluna_a, coluna_b = st.columns(2)
        nome = coluna_a.text_input("Nome do paciente")
        identificacao = coluna_b.text_input("Identificação (ID ou CPF)")
        escolha = coluna_a.selectbox("Nível de gravidade (triagem)", list(OPCOES_NIVEL))
        enfermeiro = coluna_b.text_input("Enfermeiro responsável pela triagem")
        enviado = st.form_submit_button("Cadastrar e colocar na fila")

    if enviado:
        try:
            servico.cadastrar_e_triar(nome, identificacao, OPCOES_NIVEL[escolha], enfermeiro, relogio.agora())
            st.session_state.mensagem = ("success", f"{nome.strip()} entrou na fila.")
            st.rerun()
        except ValueError as erro:
            st.error(f"Não foi possível cadastrar: {erro}")

    with st.expander("Tabela de níveis do Protocolo de Manchester"):
        st.table(pd.DataFrame([
            {"Nível": n.numero, "Cor": n.cor, "Classificação": n.descricao,
             "Tempo máximo (min)": n.tempo_max_min}
            for n in NivelManchester
        ]).set_index("Nível"))

# ----------------------------------------------------------------------
# Fila ao vivo e alertas (RN03, RN05, RN09, RN10, RN11)
# ----------------------------------------------------------------------
with aba_fila:
    st.subheader("Fila ao vivo")

    if alertas:
        for paciente in alertas:
            espera = paciente.calcular_tempo_espera(agora)
            limite = paciente.TEMPOS_MAXIMOS[paciente.nivel_original]
            st.warning(
                f"ALERTA DE SLA: {paciente.nome} ({paciente.identificacao}) espera há "
                f"{espera:.0f} min; o máximo do nível {paciente.nivel_original} é {limite} min."
            )

    estado = servico.listar_fila(agora)
    if not estado:
        st.info("A fila está vazia.")
    else:
        tabela = pd.DataFrame([
            {
                "Posição": linha["posicao"],
                "ID": linha["identificacao"],
                "Paciente": linha["nome"],
                "Cor": linha["cor"],
                "Nível original": linha["nivel_original"],
                "Nível efetivo": linha["nivel_efetivo"],
                "Promovido (aging)": "sim" if linha["nivel_efetivo"] < linha["nivel_original"] else "",
                "Espera (min)": round(linha["tempo_espera_min"], 1),
            }
            for linha in estado
        ])
        estilo = tabela.style.apply(
            lambda linha: [f"background-color: {CORES_LINHA.get(linha['Cor'], '#ffffff')}; color: #111111"] * len(linha),
            axis=1,
        )
        estilo = estilo.format({"Espera (min)": "{:.0f}"})
        st.dataframe(estilo, width="stretch", hide_index=True)
        st.caption("Ordem: nível efetivo (gravidade) e, no empate, ordem de chegada (FIFO).")

# ----------------------------------------------------------------------
# Atendimento (RN07)
# ----------------------------------------------------------------------
with aba_atendimento:
    st.subheader("Chamar paciente")
    if st.button("Chamar próximo paciente", type="primary"):
        chamado = servico.chamar_proximo(relogio.agora())
        if chamado is None:
            st.session_state.mensagem = ("info", "Não há pacientes aguardando.")
        else:
            espera = chamado.calcular_tempo_espera(relogio.agora())
            dentro = chamado.verificar_sla(relogio.agora()) == "Dentro do prazo"
            st.session_state.ultimo_chamado = (
                f"{chamado.nome} (nível original {chamado.nivel_original}, "
                f"nível efetivo {chamado.nivel_efetivo}) esperou {espera:.0f} min"
                f" - {'dentro do prazo' if dentro else 'PRAZO EXCEDIDO'}"
            )
        st.rerun()

    if st.session_state.ultimo_chamado:
        st.success(f"Chamado: {st.session_state.ultimo_chamado}")
    st.caption("O paciente chamado sai da fila e a saída é registrada no log de auditoria.")

# ----------------------------------------------------------------------
# Histórico (RN14)
# ----------------------------------------------------------------------
with aba_historico:
    st.subheader("Histórico de atendimentos")
    historico = servico.listar_historico()
    if not historico:
        st.info("Nenhum atendimento concluído ainda.")
    else:
        st.dataframe(pd.DataFrame(historico).rename(columns={
            "id": "ID", "nome": "Paciente", "enfermeiro": "Enfermeiro", "chegada": "Chegada",
            "saida": "Saída", "nivel_original": "Nível original", "nivel_efetivo": "Nível efetivo",
            "tempo_espera_min": "Espera (min)", "cumpriu_sla": "Cumpriu SLA (1=sim)",
            "tamanho_fila": "Fila após saída",
        }), width="stretch", hide_index=True)

    st.subheader("Promoções por aging")
    promocoes = repositorio.listar_promocoes()
    if not promocoes:
        st.info("Nenhuma promoção por aging registrada.")
    else:
        st.dataframe(pd.DataFrame(promocoes).rename(columns={
            "paciente_id": "ID", "nome": "Paciente", "nivel_original": "Nível original",
            "nivel_efetivo": "Nível efetivo", "horario": "Horário",
        }), width="stretch", hide_index=True)

# ----------------------------------------------------------------------
# Métricas de SLA (RN13)
# ----------------------------------------------------------------------
with aba_metricas:
    st.subheader("Métricas de SLA")
    resultado = Metricas.do_historico(servico.listar_historico()).calcular()
    if resultado["total_atendidos"] == 0:
        st.info("Atenda alguns pacientes para ver as métricas.")
    else:
        indicador1, indicador2, indicador3 = st.columns(3)
        indicador1.metric("Atendidos", resultado["total_atendidos"])
        indicador2.metric("Dentro do prazo", resultado["atendidos_no_prazo"])
        indicador3.metric("% no prazo", f"{resultado['percentual_no_prazo']}%")

        st.write("Tempo médio de espera por nível (minutos)")
        medias = pd.DataFrame({
            "Nível": [f"{n} - {NivelManchester.por_numero(n).cor}" for n in resultado["tempo_medio_por_nivel"]],
            "Espera média (min)": list(resultado["tempo_medio_por_nivel"].values()),
        }).set_index("Nível")
        st.bar_chart(medias)

# ----------------------------------------------------------------------
# Auditoria SQL (RN08, RN12)
# ----------------------------------------------------------------------
with aba_sql:
    st.subheader("Logs de auditoria em SQL")
    st.caption("Registra entradas, saídas e promoções por aging. O arquivo gerado roda depois do schema.sql.")
    if st.button("Exportar logs.sql"):
        caminho = servico.exportar_logs()
        st.session_state.mensagem = ("success", f"Arquivo gerado: {caminho}")
        st.rerun()

    from pathlib import Path
    arquivo = Path("sql") / "logs.sql"
    if arquivo.exists():
        conteudo = arquivo.read_text(encoding="utf-8")
        st.download_button("Baixar logs.sql", conteudo, file_name="logs.sql", mime="text/plain")
        st.code(conteudo[:4000], language="sql")
