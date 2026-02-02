# WORSHIP SCHEDULER - PROJECT CONTEXT

## 1. Visão Geral
Sistema de otimização de escalas para equipas de louvor, focado em resolver conflitos complexos de disponibilidade, competência técnica e fadiga dos voluntários.

* **Stack:** Python 3.11+, Google OR-Tools (CP-SAT), Pandas.
* **Paradigma:** Constraint Satisfaction Problem (CSP) com Otimização Global (Single Solve).

---

## 2. Arquitetura e Fluxo de Dados

O sistema **não** resolve a escala dia-a-dia (abordagem gulosa). Ele carrega todas as restrições e resolve o período inteiro de uma só vez para garantir a melhor alocação global.

### Fluxo de Execução
1.  **Input (CSVs):** O utilizador preenche os CSVs usando **Nomes** (para melhor UX) e datas ISO (`YYYY-MM-DD`).
2.  **Loader (`src/loader.py`):**
    * Lê os CSVs.
    * Valida se os nomes existem (proteção contra *typos*).
    * Converte internamente **Nomes → IDs**.
    * Realiza o **Merge de Demandas** (Template + Custom) para gerar a lista final de necessidades.
3.  **Solver (`src/solver.py`):**
    * Cria variáveis booleanas `x[pessoa, dia, funcao]`.
    * Aplica Hard Constraints (incluindo a Janela Deslizante).
    * Aplica Soft Constraints (preferências).
    * Executa o `Solve()` uma única vez.
4.  **Output:** Gera a escala final (Excel/CSV) traduzindo IDs de volta para Nomes.

---

## 3. Regras de Negócio (Constraints)

### Hard Constraints (Obrigatórias)
O solver **nunca** violará estas regras. Se não for possível cumpri-las, retornará `INFEASIBLE`.

1.  **Indisponibilidade:** Se um membro consta em `indisponibilidades.csv` numa data, ele não pode ser escalado.
2.  **Competência:** Um voluntário só assume funções listadas na sua coluna `roles`.
3.  **Unicidade:** Um voluntário só pode exercer uma função por evento/dia.
4.  **Janela Deslizante de Fadiga (Rolling Window):**
    * A restrição `max_shifts` (definida em `membros.csv`) aplica-se a **qualquer intervalo de 31 dias consecutivos**.
    * *Lógica:* Para cada dia `D` do calendário, a soma de escalas entre `D` e `D+30` não pode exceder o limite do membro.

### Lógica de Cobertura de Demanda (Merge Strategy)
O sistema define "quem precisamos hoje" cruzando `templates_serviços.csv` com `demandas_customizadas.csv`.
A regra é: **"O Específico (Custom) vence o Genérico (Template)"**.

* **Substituição:** Se uma função (ex: Guitarra) existe no Template mas também no Custom para aquele dia, valem os valores do Custom.
* **Adição:** Se o Custom pede uma função que não existe no Template (ex: Saxofone), ela é adicionada à demanda do dia.
* **Remoção:** Para remover uma função obrigatória do Template, o Custom deve declará-la com `max_qty = 0`.

### Soft Constraints (Otimização)
O solver tentará cumprir estas regras, mas pode violá-las se necessário.

1.  **Equidade:** Minimizar a variância de escalas entre membros da mesma função.
2.  **Evitar Dobradinhas:** Penalizar escalas em dias consecutivos (ex: Sábado + Domingo).

---

## 4. Estrutura de Dados (Inputs)

Todos os ficheiros devem estar na pasta `data/`. As datas devem seguir estritamente o formato ISO 8601: **`YYYY-MM-DD`**.

### A. Dados de Pessoas
1.  **`membros.csv`**
    * Definição dos voluntários e seus limites.
    * Colunas: `id, nome, roles, max_shifts`
    * *Nota:* `roles` separadas por ponto e vírgula (ex: `Vocal;Violao`). `max_shifts` é o limite móvel (31 dias).

2.  **`indisponibilidades.csv`**
    * Datas de bloqueio total.
    * Colunas: `nome, data`
    * *UX:* Usa o **nome** exato do membro. O loader valida e converte para ID.

### B. Dados de Calendário e Regras
3.  **`templates_serviços.csv`**
    * A "receita" padrão para tipos de cultos.
    * Colunas: `event_template, role, min_qty, max_qty`

4.  **`cultos.csv`**
    * O calendário real a ser preenchido.
    * Colunas: `data, event_template`

5.  **`demandas_customizadas.csv`**
    * Exceções pontuais.
    * Colunas: `data, role, min_qty, max_qty`
    * *Importante:* Usado para fazer override, adicionar ou remover (com max=0) demandas do template.

---

## 5. Guia de Desenvolvimento

### `src/loader.py`
* Responsável pela **Sanitização e Preparação**.
* Cria dicionário `name_to_id_map`.
* Valida nomes de indisponibilidade (lança erro se não encontrar).
* Implementa a lógica de **Merge de Dicionários** para as demandas (Template vs Custom).

### `src/solver.py`
* Responsável pela **Matemática**.
* Recebe dados limpos (com IDs e demandas já processadas).
* Implementa a lógica da Janela Deslizante (iterando `all_dates` para criar restrições de soma).

---

## 6. Estrutura de Pastas

```text
/
├── data/                   # Arquivos CSV de entrada
│   ├── membros.csv
│   ├── indisponibilidades.csv
│   ├── cultos.csv
│   ├── templates_serviços.csv
│   └── demandas_customizadas.csv
├── src/
│   ├── loader.py           # Leitura, Validação e Merge Lógico
│   ├── model.py            # Dataclasses (Pydantic)
│   ├── solver.py           # Engine OR-Tools
│   └── main.py             # Orquestrador
├── tools/                  # Scripts auxiliares
└── README.md               # Documentação Central