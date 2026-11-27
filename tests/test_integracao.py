"""
Teste de integração: roda o cenário do relatório (João, Maria e Pedro)
passando por serviço, fila, aging, SLA, métricas e logs SQL.

Rodar a partir da raiz do projeto:  python tests/test_integracao.py
"""

import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.fila_prioridade import FilaPrioridade
from src.metricas import Metricas
from src.paciente import Paciente
from src.pessoa import Pessoa
from src.repositorio_log import RepositorioLog
from src.servico_atendimento import ServicoAtendimento

H = lambda hora, minuto: datetime(2026, 12, 1, hora, minuto)


def montar_cenario():
    repo = RepositorioLog(":memory:")
    servico = ServicoAtendimento(FilaPrioridade(), repo)
    servico.cadastrar_e_triar("Joao", "J1", 4, "Enf. Marta", H(10, 0))
    servico.cadastrar_e_triar("Maria", "M1", 1, "Enf. Marta", H(10, 5))
    servico.cadastrar_e_triar("Pedro", "P1", 3, "Enf. Rogerio", H(10, 10))
    return servico, repo


def nomes(servico, agora):
    return [linha["nome"] for linha in servico.listar_fila(agora)]


def testar_ordem_por_gravidade():
    servico, _ = montar_cenario()
    assert nomes(servico, H(10, 10)) == ["Maria", "Pedro", "Joao"]
    print("OK  ordem por gravidade (Maria, Pedro, Joao)")


def testar_aging_e_limite():
    servico, _ = montar_cenario()
    # 11h00: Joao (verde, max 120) espera 60 min e sobe para o nivel 3
    assert nomes(servico, H(11, 0)) == ["Maria", "Joao", "Pedro"]
    estado = {l["nome"]: l for l in servico.listar_fila(H(11, 0))}
    assert estado["Joao"]["nivel_original"] == 4 and estado["Joao"]["nivel_efetivo"] == 3
    # muito tempo depois: ninguem passa do nivel 3 e a Maria continua primeira
    assert nomes(servico, H(20, 0))[0] == "Maria"
    assert all(l["nivel_efetivo"] >= 3 or l["nivel_original"] <= 2
               for l in servico.listar_fila(H(20, 0)))
    print("OK  aging sobe o Joao ao nivel 3 e respeita o limite")


def testar_alertas_sla():
    servico, _ = montar_cenario()
    alertas = [p.nome for p in servico.alertas_sla(H(11, 0))]
    assert "Maria" in alertas and "Pedro" not in alertas   # Pedro: 50 min de 60
    alertas = [p.nome for p in servico.alertas_sla(H(11, 20))]
    assert "Pedro" in alertas                               # 70 min > 60
    print("OK  alertas de SLA")


def testar_atendimento_logs_e_metricas():
    servico, repo = montar_cenario()
    primeiro = servico.chamar_proximo(H(11, 0))
    assert primeiro.nome == "Maria"
    assert servico.chamar_proximo(H(11, 0)).nome == "Joao"      # promovido por aging
    assert servico.chamar_proximo(H(11, 0)).nome == "Pedro"
    assert servico.chamar_proximo(H(11, 0)) is None             # fila vazia

    historico = repo.listar_historico()
    assert len(historico) == 3
    assert len(repo.listar_promocoes()) == 1                    # so o Joao subiu

    metricas = Metricas.do_historico(historico).calcular()
    assert metricas["total_atendidos"] == 3
    # Maria (max 0) estourou; Joao (60 de 120) e Pedro (50 de 60) cumpriram
    assert metricas["atendidos_no_prazo"] == 2
    assert metricas["percentual_no_prazo"] == 66.67
    print("OK  atendimento, logs e metricas")

    with tempfile.TemporaryDirectory() as pasta:
        arquivo = repo.exportar_sql(Path(pasta) / "logs.sql")
        novo = sqlite3.connect(":memory:")
        novo.executescript((RAIZ / "sql" / "schema.sql").read_text(encoding="utf-8"))
        novo.executescript(arquivo.read_text(encoding="utf-8"))
        assert novo.execute("SELECT COUNT(*) FROM log_entrada").fetchone()[0] == 3
        assert novo.execute("SELECT COUNT(*) FROM log_saida").fetchone()[0] == 3
        assert novo.execute("SELECT COUNT(*) FROM log_aging").fetchone()[0] == 1
    print("OK  logs.sql executavel")


def testar_validacoes_e_heranca():
    servico, _ = montar_cenario()
    try:
        servico.cadastrar_e_triar("Outro", "J1", 2, "Enf. Marta", H(10, 20))
        assert False, "deveria recusar identificacao repetida"
    except ValueError:
        pass
    paciente = Paciente("Ana", "A1", H(10, 0), "Enf. Marta", 3)
    assert isinstance(paciente, Pessoa)
    assert paciente.nome == "Ana" and paciente.enfermeiro.get_nome() == "Enf. Marta"
    assert paciente.descrever() == "Ana (ID A1, nivel 3)"
    print("OK  validacoes e heranca (Paciente e uma Pessoa)")


if __name__ == "__main__":
    testar_ordem_por_gravidade()
    testar_aging_e_limite()
    testar_alertas_sla()
    testar_atendimento_logs_e_metricas()
    testar_validacoes_e_heranca()
    print("\nTodos os testes de integracao passaram.")
