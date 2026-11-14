
-- schema.sql - Estrutura do banco de dados (A3 - Fila de Prioridade)
-- Pronto-socorro com Protocolo de Manchester, aging e auditoria.
-- Cobre: RN08 (log de entrada e saida) e RN12 (log de promocoes por aging)
-- Datas/horas sao guardadas como texto no formato 'AAAA-MM-DD HH:MM:SS'

-- Ficha do paciente (cadastro e triagem com enfermeiro)
CREATE TABLE IF NOT EXISTS pacientes (
    id              TEXT    PRIMARY KEY,
    nome            TEXT    NOT NULL,
    chegada         TEXT    NOT NULL,
    nivel_original  INTEGER NOT NULL CHECK (nivel_original BETWEEN 1 AND 5),
    enfermeiro      TEXT    NOT NULL
);


-- tamanho_fila = quantos pacientes ha na fila DEPOIS da entrada (estado da fila)
CREATE TABLE IF NOT EXISTS log_entrada (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id   TEXT    NOT NULL REFERENCES pacientes(id),
    horario       TEXT    NOT NULL,
    nivel         INTEGER NOT NULL CHECK (nivel BETWEEN 1 AND 5),
    tamanho_fila  INTEGER NOT NULL CHECK (tamanho_fila >= 0)
);

-- Saida da fila
-- tamanho_fila = quantos pacientes restam na fila DEPOIS da saida (estado da fila)
CREATE TABLE IF NOT EXISTS log_saida (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id       TEXT    NOT NULL REFERENCES pacientes(id),
    horario           TEXT    NOT NULL,
    tempo_espera_min  REAL    NOT NULL CHECK (tempo_espera_min >= 0),
    nivel_original    INTEGER NOT NULL CHECK (nivel_original BETWEEN 1 AND 5),
    nivel_efetivo     INTEGER NOT NULL CHECK (nivel_efetivo BETWEEN 1 AND 5),
    cumpriu_sla       INTEGER NOT NULL CHECK (cumpriu_sla IN (0, 1)),
    tamanho_fila      INTEGER NOT NULL CHECK (tamanho_fila >= 0)
);

-- Promocoes por aging 
CREATE TABLE IF NOT EXISTS log_aging (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     TEXT    NOT NULL REFERENCES pacientes(id),
    nivel_original  INTEGER NOT NULL CHECK (nivel_original BETWEEN 1 AND 5),
    nivel_efetivo   INTEGER NOT NULL CHECK (nivel_efetivo BETWEEN 1 AND 5),
    horario         TEXT    NOT NULL
);
