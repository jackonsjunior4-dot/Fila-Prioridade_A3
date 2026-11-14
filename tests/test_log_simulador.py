"""
Testes do repositorio_log.py, do schema.sql e do simulador.py.
Rodar a partir da raiz do projeto:  python tests/test_log_simulador.py
"""

import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.repositorio_log import RepositorioLog
from src.simulador import GeradorPacientes, RelogioSimulado


def testar_relogio():
    relogio = RelogioSimulado(datetime(2026, 11, 24, 10, 0))
    relogio.avancar(30)
    assert relogio.agora() == datetime(2026, 11, 24, 10, 30)
    try:
        relogio.avancar(-5)
        assert False, "deveria recusar minutos negativos"
    except ValueError:
        pass
    print("OK  relogio simulado")


def testar_gerador():
    pacientes = GeradorPacientes(semente=1).gerar(50)
    assert len(pacientes) == 50
    assert len({p["id"] for p in pacientes}) == 50          # ids unicos
    assert all(1 <= p["nivel"] <= 5 for p in pacientes)
    # mesma semente = mesmos pacientes
    assert GeradorPacientes(semente=1).gerar(5) == GeradorPacientes(semente=1).gerar(5)
    print("OK  gerador de pacientes")


def testar_repositorio_e_exportacao():
    chegada = datetime(2026, 11, 24, 10, 0)
    saida = datetime(2026, 11, 24, 12, 30)

    repo = RepositorioLog(":memory:")
    repo.registrar_entrada("P1", "Joao O'Neil", chegada, 4, "Enf. Marta", 1)
    repo.registrar_entrada("P2", "Maria", chegada, 1, "Enf. Rogerio", 2)
    repo.registrar_promocao("P1", 4, 3, datetime(2026, 11, 24, 11, 0))
    repo.registrar_saida("P2", chegada, 0, 1, 1, True, 1)
    repo.registrar_saida("P1", saida, 150, 4, 3, False, 0)

    historico = repo.listar_historico()
    assert len(historico) == 2
    assert historico[0]["nome"] == "Joao O'Neil" and historico[0]["cumpriu_sla"] == 0
    assert historico[0]["tamanho_fila"] == 0 and historico[1]["tamanho_fila"] == 1
    assert len(repo.listar_promocoes()) == 1

    # O logs.sql precisa ser executavel num banco vazio (schema + logs)
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = repo.exportar_sql(Path(pasta) / "logs.sql")
        novo = sqlite3.connect(":memory:")
        novo.executescript((RAIZ / "sql" / "schema.sql").read_text(encoding="utf-8"))
        novo.executescript(arquivo.read_text(encoding="utf-8"))
        assert novo.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0] == 2
        assert novo.execute("SELECT COUNT(*) FROM log_entrada").fetchone()[0] == 2
        assert novo.execute("SELECT COUNT(*) FROM log_aging").fetchone()[0] == 1
        assert novo.execute("SELECT COUNT(*) FROM log_saida").fetchone()[0] == 2
        nome = novo.execute("SELECT nome FROM pacientes WHERE id='P1'").fetchone()[0]
        assert nome == "Joao O'Neil"                          # aspas preservadas
        assert novo.execute(
            "SELECT tamanho_fila FROM log_entrada WHERE paciente_id='P2'").fetchone()[0] == 2
    print("OK  repositorio + logs.sql executavel")

    repo.limpar()
    assert repo.listar_historico() == []
    print("OK  limpar()")


if __name__ == "__main__":
    testar_relogio()
    testar_gerador()
    testar_repositorio_e_exportacao()
    print("\nTodos os testes passaram.")
