

from datetime import datetime


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

        if not nome or not nome.strip():
            raise ValueError("O nome é obrigatório.")

        if not identificacao or not identificacao.strip():
            raise ValueError("A identificação é obrigatória.")

        if not enfermeiro or not enfermeiro.strip():
            raise ValueError("O enfermeiro é obrigatório.")

        if not isinstance(chegada, datetime):
            raise ValueError("A chegada deve ser uma data e hora.")

        if nivel_original not in [1, 2, 3, 4, 5]:
            raise ValueError("Nível Manchester inválido.")

        self.nome = nome
        self.identificacao = identificacao
        self.chegada = chegada
        self.enfermeiro = enfermeiro
        self.nivel_original = nivel_original
        self.nivel_efetivo = nivel_original

    def calcular_tempo_espera(self, agora=None):
        if agora is None:
            agora = datetime.now()

        tempo = agora - self.chegada
        return tempo.total_seconds() / 60

    def verificar_sla(self, agora=None):
        tempo_espera = self.calcular_tempo_espera(agora)
        tempo_maximo = self.TEMPOS_MAXIMOS[self.nivel_original]

        if tempo_espera > tempo_maximo:
            return "Prazo excedido"

        return "Dentro do prazo"


    def atualizar_nivel_efetivo(self, agora=None):
        if agora is None:
            agora = datetime.now()

        if self.nivel_original <= 2:
            self.nivel_efetivo = self.nivel_original
            return self.nivel_efetivo

        tempo_espera = self.calcular_tempo_espera(agora)

        intervalo = self.TEMPOS_MAXIMOS[self.nivel_original] / 2

        promocoes = int(max(0, tempo_espera) // intervalo)

        self.nivel_efetivo = max(
            3,
            self.nivel_original - promocoes
        )

        return self.nivel_efetivo

        
