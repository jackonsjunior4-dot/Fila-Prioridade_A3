"""
simulador.py - Modo demonstracao do sistema .

Por que existe: o aging depende de horas de espera, e a demonstracao tem
poucos minutos. O relogio simulado "pula" o tempo e o gerador cria
pacientes aleatorios para o teste de estresse.
"""

import random
from datetime import datetime, timedelta

# Data/hora inicial padrao da simulacao (dia da apresentacao, 08h00).
INICIO_PADRAO = datetime(2026, 11, 24, 8, 0, 0)


class RelogioSimulado:
    """Relogio controlado: so anda quando mandamos avancar."""

    def __init__(self, inicio: datetime = INICIO_PADRAO):
        self.__agora = inicio

    def agora(self) -> datetime:
        return self.__agora

    def avancar(self, minutos: float) -> datetime:
        """Avanca o relogio e devolve o novo horario."""
        if minutos < 0:
            raise ValueError("Nao e possivel voltar no tempo: minutos deve ser >= 0.")
        self.__agora += timedelta(minutes=minutos)
        return self.__agora


class GeradorPacientes:
    """
    Cria dados de pacientes aleatorios (teste de estresse).
    Devolve apenas dados simples (dicionarios): quem for cadastrar
    (ServicoAtendimento) converte o numero para NivelManchester.
    """

    NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela",
             "Hugo", "Isabela", "Joao", "Karina", "Lucas", "Mariana", "Nicolas",
             "Olivia", "Paulo", "Rafaela", "Samuel", "Tatiane", "Vinicius"]
    SOBRENOMES = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa",
                  "Rodrigues", "Almeida", "Nascimento", "Lima", "Araujo", "Ribeiro"]
    ENFERMEIROS = ["Enf. Marta", "Enf. Rogerio", "Enf. Patricia", "Enf. Cesar"]

    # Niveis 1 a 5: em emergencia real, ha poucos vermelhos e muitos amarelos/verdes.
    NIVEIS = [1, 2, 3, 4, 5]
    PESOS = [5, 10, 30, 35, 20]

    def __init__(self, semente=None):
        # semente fixa = mesmos pacientes toda vez (bom para ensaiar a demo)
        self.__sorteio = random.Random(semente)
        self.__contador = 0

    def gerar(self, quantidade: int) -> list:
        """Devolve uma lista de dicionarios: id, nome, nivel, enfermeiro."""
        if quantidade < 0:
            raise ValueError("A quantidade deve ser >= 0.")
        pacientes = []
        for _ in range(quantidade):
            self.__contador += 1
            nome = (f"{self.__sorteio.choice(self.NOMES)} "
                    f"{self.__sorteio.choice(self.SOBRENOMES)}")
            pacientes.append({
                "id": f"SIM{self.__contador:04d}",
                "nome": nome,
                "nivel": self.__sorteio.choices(self.NIVEIS, weights=self.PESOS)[0],
                "enfermeiro": self.__sorteio.choice(self.ENFERMEIROS),
            })
        return pacientes
