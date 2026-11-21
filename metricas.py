
def calcular_metricas(atendimentos):
    """
    Calcula o percentual de atendimentos dentro do prazo
    e o tempo médio de espera por nível de prioridade.
    """

    total_atendidos = 0
    atendidos_no_prazo = 0

    # Armazena os tempos de espera separados por nível
    tempos_por_nivel = {}

    for atendimento in atendimentos:

        # Considera apenas atendimentos já concluídos
        if atendimento["status"] != "atendido":
            continue

        total_atendidos += 1

        nivel = atendimento["nivel"]
        tempo_espera = atendimento["tempo_espera"]
        prazo = atendimento["prazo"]

        # Verifica se o atendimento ocorreu dentro do prazo
        if tempo_espera <= prazo:
            atendidos_no_prazo += 1

        # Agrupa os tempos de espera por nível
        if nivel not in tempos_por_nivel:
            tempos_por_nivel[nivel] = []

        tempos_por_nivel[nivel].append(tempo_espera)

    # Calcula o percentual de atendimentos dentro do prazo
    if total_atendidos > 0:
        percentual_no_prazo = (
            atendidos_no_prazo / total_atendidos
        ) * 100
    else:
        percentual_no_prazo = 0

    # Calcula o tempo médio de espera por nível
    tempo_medio_por_nivel = {}

    for nivel, tempos in tempos_por_nivel.items():
        media = sum(tempos) / len(tempos)
        tempo_medio_por_nivel[nivel] = round(media, 2)

    # Retorna todas as métricas calculadas
    return {
        "total_atendidos": total_atendidos,
        "atendidos_no_prazo": atendidos_no_prazo,
        "percentual_no_prazo": round(percentual_no_prazo, 2),
        "tempo_medio_por_nivel": tempo_medio_por_nivel
    }
