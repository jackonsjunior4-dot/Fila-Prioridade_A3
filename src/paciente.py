from datetime import datetime, timedelta

from src.enfermeiro import Enfermeiro
from src.nivel import NivelManchester
from src.pessoa import Pessoa


class Paciente(Pessoa):
    """Ficha do paciente. Herda de Pessoa (o nome fica guardado lá)."""

    # Tempo máximo (min) de cada nível, vindo do NivelManchester.
    TEMPOS_MAXIMOS = {nivel.numero: nivel.tempo_max_min for nivel in NivelManchester}

    def __init__(
        self, nome, identificacao, chegada,
        enfermeiro, nivel_original
    ):
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("O nome e obrigatorio.")

        if not isinstance(identificacao, str) or not identificacao.strip():
            raise ValueError("A identificacao e obrigatoria.")

        # Aceita o nome do enfermeiro (texto) ou um objeto Enfermeiro.
        if isinstance(enfermeiro, Enfermeiro):
            responsavel = enfermeiro
        elif isinstance(enfermeiro, str) and enfermeiro.strip():
            responsavel = Enfermeiro(enfermeiro)
        else:
            raise ValueError("O enfermeiro e obrigatorio.")

        if not isinstance(chegada, datetime):
            raise ValueError("A chegada deve ser uma data e hora.")

        if type(nivel_original) is not int or nivel_original not in [1, 2, 3, 4, 5]:
            raise ValueError("Nivel Manchester invalido.")

        super().__init__(nome)          # herança: o nome é guardado na Pessoa
        self.identificacao = identificacao.strip()
        self.id = self.identificacao
        self.chegada = chegada
        self.__enfermeiro = responsavel

        self.nivel_original = nivel_original
        self.nivel_efetivo = nivel_original
        self.historico_aging = []

    @property
    def nome(self):
        """O nome vem da superclasse Pessoa."""
        return self.get_nome()

    @property
    def enfermeiro(self):
        """Enfermeiro que fez a triagem (objeto Enfermeiro)."""
        return self.__enfermeiro

    def descrever(self):
        """Sobrescreve Pessoa.descrever() (polimorfismo)."""
        return (
            f"{self.nome} (ID {self.identificacao}, "
            f"nivel {self.nivel_efetivo})"
        )

    def calcular_tempo_espera(self, agora=None):
        if agora is None:
            agora = datetime.now()

        if not isinstance(agora, datetime):
            raise ValueError("Horario atual invalido.")

        tempo = agora - self.chegada
        return max(0, tempo.total_seconds() / 60)

    def verificar_sla(self, agora=None):
        tempo = self.calcular_tempo_espera(agora)
        limite = self.TEMPOS_MAXIMOS[self.nivel_original]

        if tempo > limite:
            return "Prazo excedido"

        return "Dentro do prazo"

    def atualizar_nivel_efetivo(self, agora=None):
        if agora is None:
            agora = datetime.now()

        if not isinstance(agora, datetime):
            raise ValueError("Horario atual invalido.")

        # Vermelho e laranja nao sofrem aging.
        if self.nivel_original <= 2:
            return self.nivel_efetivo

        tempo = self.calcular_tempo_espera(agora)
        intervalo = self.TEMPOS_MAXIMOS[self.nivel_original] / 2

        promocoes = int(tempo // intervalo)
        novo_nivel = max(3, self.nivel_original - promocoes)

        # Registra cada promocao no horario em que deveria ocorrer.
        while self.nivel_efetivo > novo_nivel:
            self.nivel_efetivo -= 1

            numero = self.nivel_original - self.nivel_efetivo
            horario = self.chegada + timedelta(
                minutes=intervalo * numero
            )

            self.historico_aging.append({
                "nivel_original": self.nivel_original,
                "nivel_efetivo": self.nivel_efetivo,
                "timestamp": horario,
                "horario": horario
            })

        return self.nivel_efetivo
