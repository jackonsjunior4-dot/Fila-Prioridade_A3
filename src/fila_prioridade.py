from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, Optional

from src.nivel import niveis as NIVEIS_MANCHESTER


@dataclass
class _EntradaFila:
    """Controle interno de posição de chegada e auditoria na sala de espera."""

    paciente: Any
    ordem_chegada: int
    hora_entrada_fila: datetime

    @property
    def nivel_efetivo(self) -> int:
        if hasattr(self.paciente, "nivel_efetivo"):
            return int(self.paciente.nivel_efetivo)
        if hasattr(self.paciente, "nivel_original"):
            return int(self.paciente.nivel_original)
        return 5

    @property
    def hora_chegada(self) -> datetime:
        if hasattr(self.paciente, "chegada") and isinstance(self.paciente.chegada, datetime):
            return self.paciente.chegada
        return self.hora_entrada_fila

    @property
    def identificacao(self) -> str:
        for attr in ("identificacao", "id"):
            if hasattr(self.paciente, attr):
                valor = getattr(self.paciente, attr)
                if valor is not None:
                    return str(valor)
        return str(id(self.paciente))

    def chave_ordenacao(self) -> tuple[int, int, datetime]:
        """Ordena por gravidade efetiva, ordem de chegada e horário de chegada."""
        return (self.nivel_efetivo, self.ordem_chegada, self.hora_chegada)


class FilaPrioridade:
    """
    Sala de espera priorizada baseada no Protocolo de Manchester.

    - Ordena por gravidade (1 = mais grave) e ordem de chegada no empate.
    - Aplica aging respeitando o limite do nível 3.
    - Remove o paciente da fila quando ele é chamado para atendimento.
    """

    LIMITE_NIVEL_AGING: int = 3

    def __init__(
        self,
        intervalo_aging_minutos: Optional[int] = None,
        limite_nivel_aging: int = LIMITE_NIVEL_AGING,
        on_evento: Optional[Callable[[str, dict[str, Any]], None]] = None,
    ) -> None:
        if intervalo_aging_minutos is not None and intervalo_aging_minutos <= 0:
            raise ValueError("intervalo_aging_minutos deve ser maior que zero.")

        if type(limite_nivel_aging) is not int or limite_nivel_aging not in NIVEIS_MANCHESTER:
            raise ValueError("limite_nivel_aging deve ser um nível válido de Manchester (1 a 5).")

        self.intervalo_aging_minutos = intervalo_aging_minutos
        self.limite_nivel_aging = limite_nivel_aging
        self.on_evento = on_evento

        self._entradas: list[_EntradaFila] = []
        self._contador_chegada: int = 0

    def _emitir_evento(self, tipo_evento: str, dados: dict[str, Any]) -> None:
        if self.on_evento is not None:
            self.on_evento(tipo_evento, dados)

    def _ordenar(self) -> None:
        self._entradas.sort(key=lambda entrada: entrada.chave_ordenacao())

    def _promover_com_intervalo_customizado(self, entrada: _EntradaFila, agora: datetime) -> bool:
        """
        Aplica aging usando um intervalo fixo em minutos (quando configurado na fila),
        respeitando o limite do nível 3.
        """
        assert self.intervalo_aging_minutos is not None
        paciente = entrada.paciente

        if not hasattr(paciente, "nivel_efetivo") or not hasattr(paciente, "nivel_original"):
            return False

        if int(paciente.nivel_original) <= 2 or int(paciente.nivel_efetivo) <= self.limite_nivel_aging:
            return False

        tempo_espera_min = max(0.0, (agora - entrada.hora_chegada).total_seconds() / 60.0)
        promocoes_esperadas = int(tempo_espera_min // self.intervalo_aging_minutos)
        novo_nivel = max(self.limite_nivel_aging, int(paciente.nivel_original) - promocoes_esperadas)

        if novo_nivel < int(paciente.nivel_efetivo):
            intervalo_td = timedelta(minutes=self.intervalo_aging_minutos)
            while int(paciente.nivel_efetivo) > novo_nivel:
                paciente.nivel_efetivo = int(paciente.nivel_efetivo) - 1
                passo = int(paciente.nivel_original) - int(paciente.nivel_efetivo)
                horario_evento = entrada.hora_chegada + (intervalo_td * passo)
                if hasattr(paciente, "historico_aging") and isinstance(paciente.historico_aging, list):
                    paciente.historico_aging.append(
                        {
                            "nivel_original": paciente.nivel_original,
                            "nivel_efetivo": paciente.nivel_efetivo,
                            "timestamp": horario_evento,
                            "horario": horario_evento,
                        }
                    )
            return True

        return False

    def adicionar_paciente(self, paciente: Any, agora: Optional[datetime] = None) -> None:
        """Insere um paciente na fila e mantém a ordenação por prioridade e chegada."""
        if paciente is None:
            raise ValueError("O paciente não pode ser nulo.")

        if hasattr(paciente, "nivel_efetivo"):
            nivel_atual = int(paciente.nivel_efetivo)
            if nivel_atual not in NIVEIS_MANCHESTER:
                raise ValueError("Nível Manchester inválido.")

        momento_entrada = agora if isinstance(agora, datetime) else datetime.now()
        self._contador_chegada += 1

        entrada = _EntradaFila(
            paciente=paciente,
            ordem_chegada=self._contador_chegada,
            hora_entrada_fila=momento_entrada,
        )
        self._entradas.append(entrada)
        self.aplicar_aging(momento_entrada)
        self._ordenar()

        self._emitir_evento(
            "ENTRADA_FILA",
            {
                "acao": "ENTRADA",
                "identificacao": entrada.identificacao,
                "nome": getattr(paciente, "nome", None),
                "nivel_original": getattr(paciente, "nivel_original", entrada.nivel_efetivo),
                "nivel_efetivo": entrada.nivel_efetivo,
                "ordem_chegada": entrada.ordem_chegada,
                "timestamp": momento_entrada,
            },
        )

    def aplicar_aging(self, agora: Optional[datetime] = None) -> list[Any]:
        """
        Atualiza o nível efetivo dos pacientes na fila conforme o tempo de espera,
        respeitando o limite do nível 3. Retorna a lista de pacientes promovidos.
        """
        horario_ref = agora if isinstance(agora, datetime) else datetime.now()
        promovidos: list[Any] = []

        for entrada in self._entradas:
            paciente = entrada.paciente
            nivel_antes = entrada.nivel_efetivo

            if self.intervalo_aging_minutos is not None:
                alterou = self._promover_com_intervalo_customizado(entrada, horario_ref)
                nivel_depois = entrada.nivel_efetivo
            elif hasattr(paciente, "atualizar_nivel_efetivo"):
                nivel_depois = int(paciente.atualizar_nivel_efetivo(horario_ref))
                if nivel_depois < self.limite_nivel_aging and int(getattr(paciente, "nivel_original", nivel_depois)) > self.limite_nivel_aging:
                    paciente.nivel_efetivo = self.limite_nivel_aging
                    nivel_depois = self.limite_nivel_aging
                alterou = nivel_depois < nivel_antes
            else:
                alterou = False
                nivel_depois = nivel_antes

            if alterou:
                promovidos.append(paciente)
                self._emitir_evento(
                    "AGING_APLICADO",
                    {
                        "acao": "AGING",
                        "identificacao": entrada.identificacao,
                        "nome": getattr(paciente, "nome", None),
                        "nivel_anterior": nivel_antes,
                        "nivel_efetivo": nivel_depois,
                        "limite_nivel": self.limite_nivel_aging,
                        "timestamp": horario_ref,
                    },
                )

        if promovidos:
            self._ordenar()

        return promovidos

    def espiar_proximo(self, agora: Optional[datetime] = None) -> Optional[Any]:
        """Retorna o próximo paciente a ser atendido sem removê-lo da fila."""
        self.aplicar_aging(agora)
        self._ordenar()
        if not self._entradas:
            return None
        return self._entradas[0].paciente

    def chamar_proximo(self, agora: Optional[datetime] = None) -> Optional[Any]:
        """
        Aplica o aging, remove o paciente de maior prioridade da fila
        e o retorna para o serviço de atendimento.
        """
        horario_chamada = agora if isinstance(agora, datetime) else datetime.now()
        self.aplicar_aging(horario_chamada)
        self._ordenar()

        if not self._entradas:
            return None

        entrada_chamada = self._entradas.pop(0)
        paciente = entrada_chamada.paciente

        self._emitir_evento(
            "PACIENTE_CHAMADO",
            {
                "acao": "SAIDA",
                "identificacao": entrada_chamada.identificacao,
                "nome": getattr(paciente, "nome", None),
                "nivel_original": getattr(paciente, "nivel_original", entrada_chamada.nivel_efetivo),
                "nivel_efetivo": entrada_chamada.nivel_efetivo,
                "ordem_chegada": entrada_chamada.ordem_chegada,
                "hora_chegada": entrada_chamada.hora_chegada,
                "hora_chamada": horario_chamada,
                "timestamp": horario_chamada,
            },
        )
        return paciente

    def remover_paciente(self, identificacao_ou_paciente: Any, agora: Optional[datetime] = None) -> bool:
        """Remove um paciente específico da fila (ex.: evasão ou transferência)."""
        momento = agora if isinstance(agora, datetime) else datetime.now()
        for idx, entrada in enumerate(self._entradas):
            if (
                entrada.paciente is identificacao_ou_paciente
                or entrada.identificacao == str(identificacao_ou_paciente)
                or getattr(entrada.paciente, "id", None) == identificacao_ou_paciente
            ):
                removida = self._entradas.pop(idx)
                self._emitir_evento(
                    "PACIENTE_REMOVIDO",
                    {
                        "acao": "REMOCAO",
                        "identificacao": removida.identificacao,
                        "nome": getattr(removida.paciente, "nome", None),
                        "nivel_efetivo": removida.nivel_efetivo,
                        "timestamp": momento,
                    },
                )
                return True
        return False

    def listar_pacientes(self, agora: Optional[datetime] = None) -> list[Any]:
        """Retorna a lista ordenada de pacientes que aguardam na fila."""
        self.aplicar_aging(agora)
        self._ordenar()
        return [entrada.paciente for entrada in self._entradas]

    def obter_estado_fila(self, agora: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Retorna um resumo estruturado da fila para exibição no Streamlit ou logs."""
        self.aplicar_aging(agora)
        self._ordenar()
        estado: list[dict[str, Any]] = []

        for posicao, entrada in enumerate(self._entradas, start=1):
            nivel_ef = entrada.nivel_efetivo
            info_nivel = NIVEIS_MANCHESTER.get(nivel_ef, ["Desconhecido", "N/A", "N/A"])
            paciente = entrada.paciente

            estado.append(
                {
                    "posicao": posicao,
                    "identificacao": entrada.identificacao,
                    "nome": getattr(paciente, "nome", str(paciente)),
                    "nivel_original": getattr(paciente, "nivel_original", nivel_ef),
                    "nivel_efetivo": nivel_ef,
                    "cor": info_nivel[0],
                    "classificacao": info_nivel[1],
                    "ordem_chegada": entrada.ordem_chegada,
                    "chegada": entrada.hora_chegada,
                    "tempo_espera_min": (
                        paciente.calcular_tempo_espera(agora)
                        if hasattr(paciente, "calcular_tempo_espera")
                        else None
                    ),
                }
            )

        return estado

    def esta_vazia(self) -> bool:
        return len(self._entradas) == 0

    def __len__(self) -> int:
        return len(self._entradas)

    def __iter__(self) -> Iterator[Any]:
        return iter(self.listar_pacientes())
