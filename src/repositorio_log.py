"""
repositorio_log.py - Livro de registros (auditoria) do sistema.

 (entrada e saida), (promocoes por aging)  (historico).

  Regra a baixo 
  * Nenhum metodo usa datetime.now(): o horario sempre chega por parametro
    (vem do relogio simulado).
  * Os metodos recebem valores simples (texto, numero, datetime), Sem depender de outras classes
"""

import sqlite3
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_SCHEMA = RAIZ / "sql" / "schema.sql"
CAMINHO_LOGS = RAIZ / "sql" / "logs.sql"

# Ordem importa: "pacientes" vem primeiro porque os logs apontam para ele.
_TABELAS_EXPORT = [
    ("pacientes", ["id", "nome", "chegada", "nivel_original", "enfermeiro"], "chegada, id"),
    ("log_entrada", ["paciente_id", "horario", "nivel", "tamanho_fila"], "id"),
    ("log_aging", ["paciente_id", "nivel_original", "nivel_efetivo", "horario"], "id"),
    ("log_saida", ["paciente_id", "horario", "tempo_espera_min",
                   "nivel_original", "nivel_efetivo", "cumpriu_sla",
                   "tamanho_fila"], "id"),
]


def _formatar_horario(horario) -> str:
    """Converte datetime para texto 'AAAA-MM-DD HH:MM:SS'."""
    if isinstance(horario, datetime):
        return horario.strftime("%Y-%m-%d %H:%M:%S")
    return str(horario)


def _valor_sql(valor) -> str:
    """Transforma um valor Python em um literal SQL seguro."""
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return str(valor)
    # Texto: duplica aspas simples (O'Neil -> 'O''Neil')
    return "'" + str(valor).replace("'", "''") + "'"


class RepositorioLog:
    """Guarda e consulta os logs de auditoria em um banco SQLite."""

    def __init__(self, caminho_db: str = "hospital.db"):
        # check_same_thread=False: o Streamlit reexecuta o script em threads
        # diferentes e, sem isso, o SQLite reclama.
        self.__conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self.__conexao.row_factory = sqlite3.Row
        self.__criar_tabelas()

    
    # Preparacao
    
    def __criar_tabelas(self) -> None:
        """Executa o schema.sql (CREATE TABLE IF NOT EXISTS)."""
        script = CAMINHO_SCHEMA.read_text(encoding="utf-8")
        with self.__conexao:
            self.__conexao.executescript(script)

    def limpar(self) -> None:
        """Apaga todos os registros (util para reiniciar a simulacao)."""
        with self.__conexao:
            for tabela in ("log_saida", "log_aging", "log_entrada", "pacientes"):
                self.__conexao.execute(f"DELETE FROM {tabela}")

    def fechar(self) -> None:
        self.__conexao.close()

    
    # Registro de eventos 
    # ------------------------------------------------------------------
    def registrar_entrada(self, id_paciente: str, nome: str, chegada: datetime,
                          nivel: int, enfermeiro: str, tamanho_fila: int,
                          horario=None) -> None:
        """
        Grava o paciente (se novo) e o evento de entrada na fila.
        tamanho_fila = quantos pacientes ha na fila DEPOIS da entrada.
        """
        horario = chegada if horario is None else horario
        with self.__conexao:
            self.__conexao.execute(
                "INSERT OR IGNORE INTO pacientes "
                "(id, nome, chegada, nivel_original, enfermeiro) VALUES (?, ?, ?, ?, ?)",
                (id_paciente, nome, _formatar_horario(chegada), nivel, enfermeiro),
            )
            self.__conexao.execute(
                "INSERT INTO log_entrada (paciente_id, horario, nivel, tamanho_fila) "
                "VALUES (?, ?, ?, ?)",
                (id_paciente, _formatar_horario(horario), nivel, tamanho_fila),
            )

    def registrar_saida(self, id_paciente: str, horario: datetime,
                        tempo_espera_min: float, nivel_original: int,
                        nivel_efetivo: int, cumpriu_sla: bool,
                        tamanho_fila: int) -> None:
        """
        Grava o evento de saida (atendimento) com tempo de espera e SLA.
        tamanho_fila = quantos pacientes restam na fila DEPOIS da saida.
        """
        with self.__conexao:
            self.__conexao.execute(
                "INSERT INTO log_saida (paciente_id, horario, tempo_espera_min, "
                "nivel_original, nivel_efetivo, cumpriu_sla, tamanho_fila) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (id_paciente, _formatar_horario(horario), round(tempo_espera_min, 2),
                 nivel_original, nivel_efetivo, 1 if cumpriu_sla else 0, tamanho_fila),
            )

    def registrar_promocao(self, id_paciente: str, nivel_original: int,
                           nivel_efetivo: int, horario: datetime) -> None:
        """Grava uma promocao por aging (RN12)."""
        with self.__conexao:
            self.__conexao.execute(
                "INSERT INTO log_aging (paciente_id, nivel_original, nivel_efetivo, horario) "
                "VALUES (?, ?, ?, ?)",
                (id_paciente, nivel_original, nivel_efetivo, _formatar_horario(horario)),
            )

    # ---------------------------------------------------------------------
    # ---------------------------------------------
    #-----------------------------------------------------------------------
    def listar_historico(self) -> list:
        """Atendimentos concluidos, do mais recente para o mais antigo."""
        consulta = """
            SELECT p.id, p.nome, p.enfermeiro, p.chegada,
                   s.horario AS saida, s.nivel_original, s.nivel_efetivo,
                   s.tempo_espera_min, s.cumpriu_sla, s.tamanho_fila
            FROM log_saida s
            JOIN pacientes p ON p.id = s.paciente_id
            ORDER BY s.horario DESC, s.id DESC
        """
        return [dict(linha) for linha in self.__conexao.execute(consulta)]

    def listar_promocoes(self) -> list:
        """Todas as promocoes por aging registradas."""
        consulta = """
            SELECT a.paciente_id, p.nome, a.nivel_original, a.nivel_efetivo, a.horario
            FROM log_aging a
            JOIN pacientes p ON p.id = a.paciente_id
            ORDER BY a.horario DESC, a.id DESC
        """
        return [dict(linha) for linha in self.__conexao.execute(consulta)]

    # ------------------------------------------------------------------
    # Exportacao para arquivo .sql executavel
    # ------------------------------------------------------------------
    def exportar_sql(self, caminho=CAMINHO_LOGS) -> Path:
        """
        Gera o logs.sql com um INSERT para cada registro.
        Para rodar: execute primeiro o schema.sql e depois o logs.sql.
        """
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)

        linhas = [
            "-- logs.sql - Logs de auditoria (entrada, saida e aging)",
            "-- Execute o schema.sql antes deste arquivo.",
            "BEGIN TRANSACTION;",
        ]
        for tabela, colunas, ordem in _TABELAS_EXPORT:
            lista_colunas = ", ".join(colunas)
            consulta = f"SELECT {lista_colunas} FROM {tabela} ORDER BY {ordem}"
            for registro in self.__conexao.execute(consulta):
                valores = ", ".join(_valor_sql(registro[c]) for c in colunas)
                linhas.append(f"INSERT INTO {tabela} ({lista_colunas}) VALUES ({valores});")
        linhas.append("COMMIT;")

        caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return caminho
