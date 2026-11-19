
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
