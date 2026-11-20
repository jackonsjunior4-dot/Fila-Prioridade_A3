"""
enfermeiro.py - Profissional que faz a triagem (RN02).

Herda de Pessoa: já ganha o nome e acrescenta a matrícula (opcional).
"""

from src.pessoa import Pessoa


class Enfermeiro(Pessoa):
    """Enfermeiro responsável por classificar o paciente no Manchester."""

    def __init__(self, nome: str, matricula: str = ""):
        super().__init__(nome)                    # reaproveita o código da Pessoa
        self.__matricula = (matricula or "").strip()

    def get_matricula(self) -> str:
        return self.__matricula

    def descrever(self) -> str:
        """Sobrescreve Pessoa.descrever()."""
        base = f"Enf. {self.get_nome()}"
        if self.__matricula:
            return f"{base} (matrícula {self.__matricula})"
        return base
