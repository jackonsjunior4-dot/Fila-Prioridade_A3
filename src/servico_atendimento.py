from datetime import datetime

from src.fila_prioridade import FilaPrioridade
from src.paciente import Paciente


class ServicoAtendimento:
    """
    Coordena o atendimento: recebe o paciente, coloca na fila, chama o
    próximo e registra tudo (entrada, saída e aging) no RepositorioLog.

    Composição: o serviço é feito de uma FilaPrioridade e de um RepositorioLog.
    O horário (agora) vem sempre de fora, do relógio simulado.
    """

    def __init__(self, fila=None, repositorio=None):
        self.__fila = fila if fila is not None else FilaPrioridade()
        self.__repositorio = repositorio
        self.__ids_usados = set()
        self.__promocoes_registradas = {}

    @property
    def fila(self):
        return self.__fila

    @property
    def repositorio(self):
        return self.__repositorio

    # ------------------------------------------------------------------
    # Cadastro, triagem e entrada na fila (RN01, RN02, RN08)
    # ------------------------------------------------------------------
    def cadastrar_e_triar(self, nome, identificacao, nivel, enfermeiro, agora):
        """Cadastra o paciente, registra a triagem e coloca na fila."""
        paciente = Paciente(nome, identificacao, agora, enfermeiro, nivel)
        self.receber_paciente(paciente, agora)
        return paciente

    def receber_paciente(self, paciente, agora=None):
        if not isinstance(paciente, Paciente):
            raise ValueError("Paciente invalido.")

        if paciente.identificacao in self.__ids_usados:
            raise ValueError("Identificacao ja cadastrada.")

        agora = paciente.chegada if agora is None else agora

        # Atualiza o aging de quem já espera antes de mexer na fila.
        self.aplicar_aging(agora)
        self.__fila.adicionar_paciente(paciente, agora)
        self.__ids_usados.add(paciente.identificacao)

        if self.__repositorio is not None:
            self.__repositorio.registrar_entrada(
                paciente.identificacao,
                paciente.nome,
                paciente.chegada,
                paciente.nivel_original,
                paciente.enfermeiro.get_nome(),
                len(self.__fila),
                agora,
            )

        print("Paciente encaminhado para a fila:", paciente.nome)

    # ------------------------------------------------------------------
    # Aging (RN10, RN11, RN12)
    # ------------------------------------------------------------------
    def aplicar_aging(self, agora):
        """Aplica o aging na fila e grava no log cada promoção nova."""
        promovidos = self.__fila.aplicar_aging(agora)

        for paciente in promovidos:
            feitas = self.__promocoes_registradas.get(paciente.identificacao, 0)
            novas = paciente.historico_aging[feitas:]

            if self.__repositorio is not None:
                for evento in novas:
                    self.__repositorio.registrar_promocao(
                        paciente.identificacao,
                        evento["nivel_original"],
                        evento["nivel_efetivo"],
                        evento["horario"],
                    )

            self.__promocoes_registradas[paciente.identificacao] = len(
                paciente.historico_aging
            )

        return promovidos

    # ------------------------------------------------------------------
    # Atendimento (RN07, RN08)
    # ------------------------------------------------------------------
    def chamar_proximo(self, agora=None):
        agora = datetime.now() if agora is None else agora

        self.aplicar_aging(agora)
        paciente = self.__fila.chamar_proximo(agora)

        if paciente is None:
            print("Não há pacientes aguardando.")
            return None

        espera = paciente.calcular_tempo_espera(agora)
        cumpriu = paciente.verificar_sla(agora) == "Dentro do prazo"

        if self.__repositorio is not None:
            self.__repositorio.registrar_saida(
                paciente.identificacao,
                agora,
                espera,
                paciente.nivel_original,
                paciente.nivel_efetivo,
                cumpriu,
                len(self.__fila),
            )

        print("Chamando paciente:", paciente.nome)
        return paciente

    # ------------------------------------------------------------------
    # Alertas de SLA (RN09)
    # ------------------------------------------------------------------
    def verificar_sla(self, paciente, agora=None):
        situacao = paciente.verificar_sla(agora)

        if situacao == "Prazo excedido":
            print("ALERTA DE SLA!")
            print("Paciente:", paciente.nome)
            return True
        else:
            print("Paciente dentro do prazo.")
            return False

    def verificar_alertas(self, pacientes, agora=None):
        alertas = []

        for paciente in pacientes:
            if self.verificar_sla(paciente, agora):
                alertas.append(paciente)

        return alertas

    def alertas_sla(self, agora):
        """Pacientes que estão na fila e já passaram do tempo máximo."""
        self.aplicar_aging(agora)
        return [
            paciente
            for paciente in self.__fila.listar_pacientes(agora)
            if paciente.verificar_sla(agora) == "Prazo excedido"
        ]

    # ------------------------------------------------------------------
    # Consultas para a interface
    # ------------------------------------------------------------------
    def listar_fila(self, agora):
        """Estado da fila, já ordenada, para mostrar na tela."""
        self.aplicar_aging(agora)
        return self.__fila.obter_estado_fila(agora)

    def tamanho_fila(self):
        return len(self.__fila)

    def listar_historico(self):
        if self.__repositorio is None:
            return []
        return self.__repositorio.listar_historico()

    def exportar_logs(self, caminho=None):
        """Gera o arquivo logs.sql com tudo que foi registrado."""
        if self.__repositorio is None:
            raise ValueError("Nao ha repositorio de logs configurado.")
        if caminho is None:
            return self.__repositorio.exportar_sql()
        return self.__repositorio.exportar_sql(caminho)
