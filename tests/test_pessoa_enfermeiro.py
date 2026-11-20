"""
Testes da herança (Pessoa -> Enfermeiro) e de como o Paciente deve herdar.
Rodar a partir da raiz do projeto:  python tests/test_pessoa_enfermeiro.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.enfermeiro import Enfermeiro
from src.pessoa import Pessoa


class PacienteExemplo(Pessoa):
    """Só para demonstrar o padrão: o Paciente real faz o mesmo."""

    def __init__(self, id_paciente: str, nome: str):
        super().__init__(nome)
        self.__id = id_paciente

    def descrever(self) -> str:
        return f"{self.get_nome()} (ID {self.__id})"


def testar_pessoa():
    p = Pessoa("Maria")
    assert p.get_nome() == "Maria" and str(p) == "Maria"
    for invalido in ("", "   ", None):
        try:
            Pessoa(invalido)
            assert False, "deveria recusar nome vazio"
        except ValueError:
            pass
    print("OK  Pessoa")


def testar_enfermeiro():
    e = Enfermeiro("Marta", "COREN-123")
    assert isinstance(e, Pessoa)                       # herança
    assert e.get_nome() == "Marta"                     # método herdado
    assert e.get_matricula() == "COREN-123"
    assert e.descrever() == "Enf. Marta (matrícula COREN-123)"   # sobrescrito
    assert Enfermeiro("Rogerio").descrever() == "Enf. Rogerio"
    print("OK  Enfermeiro herda de Pessoa")


def testar_polimorfismo():
    grupo = [Enfermeiro("Marta"), PacienteExemplo("P1", "Joao")]
    textos = [pessoa.descrever() for pessoa in grupo]
    assert textos == ["Enf. Marta", "Joao (ID P1)"]    # cada um se descreve do seu jeito
    print("OK  polimorfismo (descrever)")


if __name__ == "__main__":
    testar_pessoa()
    testar_enfermeiro()
    testar_polimorfismo()
    print("\nTodos os testes passaram.")
