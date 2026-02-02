# WORSHIP SCHEDULER - PROJECT CONTEXT

## 1. Stack Tecnológica

* **Core:** Python 3.11+
* **Solver Engine:** Google OR-Tools (`ortools.sat.python.cp_model`)
* **Data Manipulation:** Pandas (`pandas`) para I/O de CSV e pré-processamento.
* **Ambiente:** Execução local (CLI/Script), desenvolvida no VS Code.

## 2. Arquitetura

* **Paradigma:** Constraint Satisfaction Problem (CSP) / Programação por Restrições.
* **Modelo de Decisão:** Matriz Tridimensional de Variáveis Booleanas.
* `x[pessoa, data, funcao]`: 1 se escalado, 0 caso contrário.


* **Fluxo de Dados:**
1. **Ingestion:** Leitura de `data/*.csv` (Pessoas, Calendário, Disponibilidade).
2. **Modeling:** Criação do `cp_model.CpModel` e aplicação de *Hard/Soft Constraints*.
3. **Solving:** Execução do `cp_model.CpSolver`.
4. **Export:** Transformação da solução em `escala_final.xlsx` ou `.csv`.



## 3. Regras de Negócio Críticas (Constraints)

### Hard Constraints (Obrigatórias)

1. **Disponibilidade:** Se `disponibilidade.csv` marca data como "NO", a variável deve ser forçada a 0.
2. **Competência:** Um voluntário só pode ser escalado para funções listadas em sua coluna `roles`.
3. **Cobertura de Demanda:** Cada culto (evento) deve ter exatamente `min_qty` e `max_qty` por função (ex: 1 Baterista, 2-3 Vocais).
4. **Unicidade:** Um voluntário não pode exercer mais de uma função no mesmo culto (exceto se explicitamente permitido).

### Soft Constraints (Preferências/Otimização)

1. **Distribuição de Carga:** Minimizar a variância de turnos entre membros da mesma função (Equidade).
2. **Descanso:** Penalizar ou proibir escalas em semanas consecutivas (configurável).
3. **Limite Mensal:** Respeitar o `max_shifts` definido por pessoa.

## 4. Estrutura de Dados (Inputs via CSV)

* `pessoas.csv`: `id, nome, roles (sep=;), max_shifts`
* `calendario.csv`: `data, evento_tipo, role_required, min, max` (Gerado automaticamente via script `tools/`)
* `disponibilidade.csv`: `pessoa_id, data, status (NO/MAYBE)`

## 5. Padrões de Código & Style Guide

* **Sintaxe OR-Tools:**
* Use `model.NewBoolVar` para variáveis de decisão.
* Use `model.Add(sum(...) == 1)` para restrições lineares.
* Use `OnlyEnforceIf` para lógica condicional complexa.


* **Estruturas Python:**
* Use **Type Hinting** estrito (`def func(df: pd.DataFrame) -> None:`).
* Use `dict` com tuplas como chaves para acesso rápido às variáveis do solver: `shifts[(p_id, date, role)]`. NÃO use listas aninhadas ou matrizes numéricas puras.


* **Modularidade:** Separe a definição do modelo (`solver_engine.py`) do carregamento de dados (`loader.py`).

## 6. Estrutura de Pastastext

/
├── data/               # CSVs de entrada e saída
├── src/
│   ├── model.py        # Dataclasses (Person, Event)
│   ├── loader.py       # Leitura Pandas e limpeza
│   ├── solver.py       # Lógica CP-SAT (Core)
│   └── exporter.py     # Geração de relatório final
├── tools/
│   └── calendar_gen.py # Script auxiliar para gerar datas (Dom/Qua)
└── main.py             # Entry point