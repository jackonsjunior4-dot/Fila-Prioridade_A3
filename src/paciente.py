
from datetime import datetime, timedelta


class Paciente:
    TEMPOS_MAXIMOS = {
        1: 0,
        2: 10,
        3: 60,
        4: 120,
        5: 240
    }

    def __init__(self, nome, identificacao, chegada,
                 enfermeiro, nivel_original):

        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("O nome e obrigatorio.")

        if not isinstance(identificacao, str) or not identificacao.strip():
            raise ValueError("A identificacao e obrigatoria.")

        if not isinstance(enfermeiro, str) or not enfermeiro.strip():
            raise ValueError("O enfermeiro e obrigatorio.")

        if not isinstance(chegada, datetime):
            raise ValueError("A chegada deve ser uma data e hora.")

        if type(nivel_original) is not int or nivel_original not in [1, 2, 3, 4, 5]:
            raise ValueError("Nivel Manchester invalido.")

        self.nome = nome.strip()
        self.identificacao = identificacao.strip()
        self.chegada = chegada
        self.enfermeiro = enfermeiro.strip()

        self.nivel_original = nivel_original
        self.nivel_efetivo = nivel_original

        self.historico_aging = []

    def calcular_tempo_espera(self, agora=None):
        if agora is None:
            agora = datetime.now()

        if not isinstance(agora, datetime):
            raise ValueError("O horario atual deve ser uma data e hora.")

        tempo = agora - self.chegada

        return max(0, tempo.total_seconds() / 60)

    def verificar_sla(self, agora=None):
        tempo_espera = self.calcular_tempo_espera(agora)

        tempo_maximo = self.TEMPOS_MAXIMOS[self.nivel_original]

        if tempo_espera > tempo_maximo:
            return "Prazo excedido"

        return "Dentro do prazo"

    def atualizar_nivel_efetivo(self, agora=None):
        if agora is None:
            agora = datetime.now()

        if not isinstance(agora, datetime):
            raise ValueError("O horario atual deve ser uma data e hora.")

        # Niveis vermelho e laranja nao sofrem aging.
        if self.nivel_original <= 2:
            return self.nivel_efetivo

        tempo_espera = self.calcular_tempo_espera(agora)

        intervalo = self.TEMPOS_MAXIMOS[self.nivel_original] / 2

        if intervalo <= 0:
            return self.nivel_efetivo

        quantidade_promocoes = int(tempo_espera // intervalo)

        novo_nivel = max(
            3,
            self.nivel_original - quantidade_promocoes
        )

        # Registra cada promocao realizada.
        while self.nivel_efetivo > novo_nivel:
            self.nivel_efetivo -= 1

            momento_promocao = self.chegada + timedelta(
                minutes=intervalo * (
                    self.nivel_original - self.nivel_efetivo
                )
            )

            self.historico_aging.append({
                "nivel_original": self.nivel_original,
                "nivel_efetivo": self.nivel_efetivo,
                "timestamp": momento_promocao.isoformat()
            })

        return self.nivel_efetivo
