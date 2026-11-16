
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
            raise ValueError("O nome é obrigatório.")

        if not isinstance(identificacao, str) or not identificacao.strip():
            raise ValueError("A identificação é obrigatória.")

        if not isinstance(enfermeiro, str) or not enfermeiro.strip():
            raise ValueError("O enfermeiro é obrigatório.")

        if not isinstance(chegada, datetime):
            raise ValueError("A chegada deve ser uma data e hora.")

        if type(nivel_original) is not int or nivel_original not in [1, 2, 3, 4, 5]:
            raise ValueError("Nível Manchester inválido.")

        self.nome = nome
        self.identificacao = identificacao
        self.chegada = chegada
        self.enfermeiro = enfermeiro
        self.nivel_original = nivel_original
        self.nivel_efetivo = nivel_original
        self.historico_aging = []

    def calcular_tempo_espera(self, agora=None):
        if agora is None:
            agora = datetime.now()

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

        if self.nivel_original <= 2:
            return self.nivel_efetivo

        tempo_espera = self.calcular_tempo_espera(agora)
        intervalo = self.TEMPOS_MAXIMOS[self.nivel_original] / 2
        promocoes = int(tempo_espera // intervalo)

        novo_nivel = max(3, self.nivel_original - promocoes)

        while self.nivel_efetivo > novo_nivel:
            self.nivel_efetivo -= 1

            self.historico_aging.append({
                "nivel_original": self.nivel_original,
                "nivel_efetivo": self.nivel_efetivo,
                "timestamp": agora.isoformat()
            })

        return self.nivel_efetivo


# TESTES DO PROJETO

agora = datetime.now()

# Teste 1: paciente azul esperando 120 minutos
azul = Paciente(
    "Joao", "12345",
    agora - timedelta(minutes=120),
    "Maria", 5
)

print("TESTE 1 - PACIENTE AZUL")
print("Nivel original:", azul.nivel_original)
print("Nivel efetivo:", azul.atualizar_nivel_efetivo(agora))
print("Historico:", azul.historico_aging)

# Teste 2: paciente verde esperando 60 minutos
verde = Paciente(
    "Carlos", "67890",
    agora - timedelta(minutes=60),
    "Maria", 4
)

print("\nTESTE 2 - PACIENTE VERDE")
print("Nivel original:", verde.nivel_original)
print("Nivel efetivo:", verde.atualizar_nivel_efetivo(agora))

# Teste 3: paciente amarelo não pode subir
amarelo = Paciente(
    "Pedro", "11111",
    agora - timedelta(minutes=180),
    "Maria", 3
)

print("\nTESTE 3 - PACIENTE AMARELO")
print("Nivel original:", amarelo.nivel_original)
print("Nivel efetivo:", amarelo.atualizar_nivel_efetivo(agora))

# Teste 4: paciente laranja não sofre aging
laranja = Paciente(
    "Ana", "22222",
    agora - timedelta(minutes=60),
    "Maria", 2
)

print("\nTESTE 4 - PACIENTE LARANJA")
print("Nivel original:", laranja.nivel_original)
print("Nivel efetivo:", laranja.atualizar_nivel_efetivo(agora))
