"""
pessoa.py - Classe base (superclasse) de quem participa do atendimento.

Herança: Paciente e Enfermeiro "são" uma Pessoa. O que é comum aos dois
(o nome) fica aqui, e cada subclasse acrescenta o que é só dela.
"""


class Pessoa:
    """Superclasse: guarda o nome e sabe se apresentar."""

    def __init__(self, nome: str):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("O nome não pode ficar vazio.")
        self.__nome = nome            # privado: só se acessa pelos métodos

    def get_nome(self) -> str:
        return self.__nome

    def descrever(self) -> str:
        """Texto de apresentação. As subclasses sobrescrevem (polimorfismo)."""
        return self.__nome

    def __str__(self) -> str:
        return self.descrever()
