
# Fila de Prioridade - Emergência Hospitalar

Simulador de fila de prioridade para emergência hospitalar, com Protocolo de Manchester, aging contra starvation, monitoramento de SLA e logs de auditoria em SQL.

Projeto A3 de Programação de Soluções Computacionais (UNIFACS).

## Integrantes

- Thalles Mendes
- Fernando de Andrade Santos
- Larissa Aparecida Bairon da Silva Sena
- João Jackson dos Santos Reis Junior
- Emanuel Barbosa Oliveira
- Fernando Carvalho Bandeira Junior

## Como executar

1. Instale o Python 3.10 ou superior.
2. Clone o repositório:

```bash
git clone https://github.com/jackonsjunior4-dot/Fila-Prioridade_A3.git
```

3. Entre na pasta:

```bash
cd Fila-Prioridade_A3
```

4. Instale as dependências:

```bash
pip install -r requirements.txt
```

5. Rode o sistema:

```bash
streamlit run app.py
```

## Regras de negócio

O sistema implementa as regras RN01 a RN15: cadastro, triagem pelo Protocolo de Manchester (5 níveis), ordenação por gravidade com FIFO no empate, tempo máximo por nível (SLA), aging com limite no nível 3, logs de auditoria, métricas, histórico e modo de simulação. A descrição completa está no relatório técnico.

## Estrutura do projeto

- `src/`: classes do sistema (nivel, paciente, fila_prioridade, servico_atendimento, metricas, repositorio_log, simulador)
- `sql/`: `schema.sql` (tabelas) e `logs.sql` (logs de auditoria gerados pelo sistema)
- `tests/`: testes automatizados
- `app.py`: interface em Streamlit

## Documentação

- Relatório técnico: (link em breve)
- Diagrama de classes UML: (link em breve)


## Testes

```bash
python tests/test_log_simulador.py
python tests/test_pessoa_enfermeiro.py
python tests/test_integracao.py
```

O `test_integracao.py` roda o cenário do relatório (João, Maria e Pedro): ordem por gravidade, aging, limite do nível 3, alertas de SLA, atendimento, métricas e `logs.sql` executável.
