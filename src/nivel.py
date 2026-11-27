
# ARQUIVO: nivel.py
# NIVEIS DE GRAVIDADE HOSPITALAR

niveis = {
    1: ["Vermelho", "Emergência", "Imediato"],
    2: ["Laranja", "Muito urgente", "10 minutos"],
    3: ["Amarelo", "Urgente", "60 minutos"],
    4: ["Verde", "Pouco urgente", "120 minutos"],
    5: ["Azul", "Não urgente", "240 minutos"]
}


def consultar_nivel(numero):

    if numero in niveis:
        dados = niveis[numero]

        print("Nível:", numero)
        print("Cor:", dados[0])
        print("Classificação:", dados[1])
        print("Tempo máximo:", dados[2])

    else:
        print("Nível inválido!")


def mostrar_niveis():

    print("=== NÍVEIS DE GRAVIDADE ===")

    for numero, dados in niveis.items():
        print("\nNível:", numero)
        print("Cor:", dados[0])
        print("Classificação:", dados[1])
        print("Tempo máximo:", dados[2])


# ---------------------------------------------------------------------------
# Classe NivelManchester (usada pelo Paciente, pela fila e pelas métricas)
# Os dicionários e funções acima continuam valendo; esta classe organiza os
# mesmos dados como objetos, com número, cor e tempo máximo (em minutos).
# ---------------------------------------------------------------------------
from enum import Enum


class NivelManchester(Enum):
    """Os 5 níveis do Protocolo de Manchester (1 = mais urgente)."""

    VERMELHO = (1, "Vermelho", "Emergência", 0)
    LARANJA = (2, "Laranja", "Muito urgente", 10)
    AMARELO = (3, "Amarelo", "Urgente", 60)
    VERDE = (4, "Verde", "Pouco urgente", 120)
    AZUL = (5, "Azul", "Não urgente", 240)

    def __init__(self, numero, cor, descricao, tempo_max_min):
        self.numero = numero
        self.cor = cor
        self.descricao = descricao
        self.tempo_max_min = tempo_max_min

    @classmethod
    def por_numero(cls, numero):
        """Devolve o nível pelo número (1 a 5)."""
        for nivel in cls:
            if nivel.numero == numero:
                return nivel
        raise ValueError("Nivel Manchester invalido.")

