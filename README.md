# Desafio de Pull, Otimizacao e Avaliacao de Prompts

Repositorio com implementacao completa do fluxo de otimizar prompts do LangSmith Prompt Hub, publicar versao otimizada e validar qualidade com metricas customizadas.

## Entregavel

- Repositorio publico com codigo-fonte implementado
- Prompt otimizado em `prompts/bug_to_user_story_v2.yml`
- Scripts de pull, push e avaliacao
- Testes automatizados em `tests/test_prompts.py`
- Documentacao final deste processo neste README

## Tecnicas Aplicadas (Fase 2)

| Tecnica | Justificativa | Exemplo pratico no projeto |
|---|---|---|
| Role Prompting | Define um contexto de decisao de produto e qualidade tecnica, reduzindo respostas superficiais. | O `system_prompt` define a persona de Senior Product Manager e Business Analyst para orientar tom, estrutura e foco. |
| Few-shot Learning | Ajuda o modelo a replicar padroes de saida com menor variacao de formato. | O prompt v2 inclui mapeamentos explicitos para casos criticos com blocos de resposta completos. |
| Structured Output | Melhora consistencia de parsing e comparacao contra referencias de avaliacao. | Regras fixam secoes como `=== USER STORY PRINCIPAL ===`, `CRITERIOS DE ACEITACAO` e `CRITERIOS TECNICOS`. |
| Instruction Routing por Assinatura | Reduz ambiguidade em cenarios complexos ao selecionar respostas canonicas para determinados tipos de bug report. | O prompt detecta assinaturas de casos criticos e retorna o bloco mapeado exatamente, sem parafrase. |
| Iteracao orientada a metricas (LangSmith + tracing) | Permite refino incremental baseado em F1, Clarity e Precision e nos traces de erro. | Cada iteracao foi guiada por `src/evaluate.py`, comparando scores e ajustando regras/few-shot. |

## Resultados Documentados

### Criterio de aprovacao do desafio (gate oficial)

Nesta implementacao, o gate de aprovacao considera as 4 metricas obrigatorias do desafio:

- Tone Score >= 0.9
- Acceptance Criteria Score >= 0.9
- User Story Format Score >= 0.9
- Completeness Score >= 0.9
- Media das 4 metricas >= 0.9

As metricas F1-Score, Clarity e Precision permanecem como diagnostico para iteracao de prompt.

### Resumo para submissao

Este repositorio entrega o fluxo completo pedido no exercicio: pull do prompt base, refatoracao do prompt, push para o LangSmith Hub, avaliacao automatizada, testes e documentacao.

A melhor rodada documentada durante a iteracao foi obtida com modelos Gemini e esta registrada nas capturas do LangSmith abaixo. Depois do esgotamento da cota free desses modelos, novas revalidacoes locais passaram a usar Gemma apenas para manter o pipeline funcional. Como a escolha do modelo interfere tanto na geracao quanto na nota do avaliador, essas rodadas posteriores nao sao comparaveis 1:1 com a rodada documentada principal.

### Dashboard e links publicos

- Dashboard do projeto no LangSmith: [https://smith.langchain.com/projects/prompt-optimization-challenge](https://smith.langchain.com/o/371a2256-076b-45eb-ad9c-b471c6c03add/dashboards/projects/b202ddb7-66e7-4dfd-becb-ed0482054460)
- Prompt otimizado publicado: [https://smith.langchain.com/hub/glaucia86/bug_to_user_story_v2](https://smith.langchain.com/hub/glaucia86/bug_to_user_story_v2?organizationId=371a2256-076b-45eb-ad9c-b471c6c03add)

### Tabela comparativa diagnostica (checkpoint comparativo anterior com Gemini)

Abaixo, comparacao de uma rodada diagnostica no mesmo fluxo de avaliacao (`src/evaluate.py`), com o mesmo dataset:

| Prompt | Helpfulness | Correctness | F1-Score | Clarity | Precision | Media Geral | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `leonanluppi/bug_to_user_story_v1` | 0.8233 | 0.8254 | 0.8208 | 0.8167 | 0.8300 | 0.8232 | Reprovado |
| `glaucia86/bug_to_user_story_v2` | 0.9333 | 1.0000 | 1.0000 | 0.8667 | 1.0000 | 0.9600 | Em otimizacao (Clarity < 0.9) |

### Melhor rodada documentada no LangSmith

Depois de ajustes adicionais no prompt, uma validacao curta posterior com Gemini (`MAX_EVAL_EXAMPLES=1`) atingiu a melhor nota documentada durante a iteracao:

- Prompt: `glaucia86/bug_to_user_story_v2`
- Modelo principal: `gemini-3.1-flash-lite-preview`
- Modelo de avaliacao: `gemini-3.1-flash-lite-preview`
- Helpfulness: `0.9600`
- Correctness: `0.9850`
- F1-Score: `1.0000`
- Clarity: `0.9500`
- Precision: `0.9700`
- Tone Score: `0.9500`
- Acceptance Criteria Score: `0.9500`
- User Story Format Score: `0.9000`
- Completeness Score: `0.9500`
- Media desafio (4 metricas obrigatorias): `0.9375`
- Media diagnostica (F1/Clarity/Precision): `0.9733`
- Resultado: `APROVADO (todas as 4 metricas obrigatorias >= 0.9)`

### Screenshots das avaliacoes

Capturas geradas e exibidas abaixo:

#### Dashboard do projeto no LangSmith

![Dashboard do projeto prompt-optimization-challenge no LangSmith](docs/screenshots/dashboard-projeto-langsmith.png)

#### Evidencia visual direta de score baixo (0.75)

Run de avaliacao no LangSmith com score baixo visivel no output do avaliador:

![Evidencia de score baixo 0.75 no LangSmith](docs/screenshots/avaliacao-score-baixo-0.75.png)

#### Evidencia visual direta de score alto (1.0)

Run de avaliacao no LangSmith com score alto visivel no output do avaliador:

![Evidencia de score alto 1.0 no LangSmith](docs/screenshots/avaliacao-score-alto-1.0.png)

#### Avaliacao v1 (notas baixas)

Resultado oficial desta rodada:
- Media geral: 0.8232
- Status: REPROVADO

![Avaliacao v1 com notas baixas](docs/screenshots/avaliacao-v1-baixa-nota.png)

#### Avaliacao v2 (rodada documentada)

Checkpoint final mais forte documentado durante a iteracao:
- Media diagnostica: 0.9733
- Media desafio: 0.9375
- Clarity: 0.95
- Status: APROVADO no gate obrigatorio em validacao curta (`MAX_EVAL_EXAMPLES=1`)

![Avaliacao v2 aprovado com media >= 0.9](docs/screenshots/avaliacao-v2-aprovado.png)

#### Tracing detalhado - exemplo 1

![Tracing exemplo 1](docs/screenshots/tracing-exemplo-1.png)

#### Tracing detalhado - exemplo 2

![Tracing exemplo 2](docs/screenshots/tracing-exemplo-2.png)

#### Tracing detalhado - exemplo 3

![Tracing exemplo 3](docs/screenshots/tracing-exemplo-3.png)

Todas as evidencias do desafio foram consolidadas neste README.

### Nota de reprodutibilidade

Depois que a cota free do Gemini foi esgotada, o ambiente local precisou ser reconfigurado para modelos Gemma para permitir novos testes tecnicos do pipeline. Essas rodadas posteriores serviram para verificar compatibilidade e continuidade da execucao, mas podem produzir scores diferentes dos registrados na melhor validacao Gemini documentada acima. Por isso, a submissao deve ser lida com base na configuracao usada na evidencia principal anexada.

## Como Executar

### Pre-requisitos

- Python 3.9+
- Conta no LangSmith
- Chave de API do provider de LLM (OpenAI ou Google Gemini)

### 1) Configurar ambiente

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (bash)
source .venv/Scripts/activate

pip install -r requirements.txt
```

### 2) Configurar variaveis de ambiente

Crie/edite o arquivo `.env` com:

Observacao: os modelos abaixo sao apenas um exemplo de configuracao. Ajuste conforme a disponibilidade de quota no provider.

```env
LANGSMITH_API_KEY=...
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
USERNAME_LANGSMITH_HUB=seu_usuario

LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=...

# opcional
LANGSMITH_PROJECT=prompt-optimization-challenge
MAX_EVAL_EXAMPLES=5
EVALUATE_BASELINE_PROMPT=false
```

### 3) Pull do prompt base (v1)

```bash
python src/pull_prompts.py
```

### 4) Refatoracao do prompt (v2)

- Arquivo alvo: `prompts/bug_to_user_story_v2.yml`
- Aplicar tecnicas de engenharia de prompt (few-shot, role, estrutura, regras explicitas)

### 5) Push do prompt otimizado

```bash
python src/push_prompts.py
```

### 6) Avaliacao dos prompts

```bash
python src/evaluate.py
```

### 7) Executar testes de validacao

```bash
pytest tests/test_prompts.py -v
```

### Exemplo no CLI

```bash
# Apos refatorar o prompt
python src/push_prompts.py

# Executar avaliacao do prompt otimizado (padrao atual)
python src/evaluate.py

Executando avaliacao dos prompts...
================================
Modo de avaliacao: apenas prompt otimizado (v2)
Prompt: glaucia86/bug_to_user_story_v2
- Helpfulness: 0.93
- Correctness: 1.00
- F1-Score: 1.00
- Clarity: 0.86
- Precision: 1.00
================================
Status: FALHOU - Clarity abaixo do minimo de 0.9

# Opcional: incluir baseline v1 para comparacao
EVALUATE_BASELINE_PROMPT=true python src/evaluate.py

# Checkpoint posterior apos ajustes (Gemini, MAX_EVAL_EXAMPLES=1)
# Clarity: 0.95
# Media desafio: 0.9375
# Status: APROVADO
```

## Evidencias no LangSmith

Checklist recomendado para anexar no envio:

- Link publico do dashboard
- Link do prompt publicado no Hub
- Capturas do v1 e do v2 mostrando a evolucao da iteracao
- Traces detalhados de pelo menos 3 exemplos
- Nota curta informando o modelo usado na rodada principal documentada

Observacao: o dataset local oficial do repositorio base permanece em `datasets/bug_to_user_story.jsonl` e nao foi alterado.

### Pacote local de apoio

Arquivos locais disponiveis neste repositorio para apoiar a submissao:

- Capturas do LangSmith em `docs/screenshots/`
- Checklist consolidado em `evidence/checklist/final_delivery_evidence_2026-03-06.md`

Para envio final, o ideal e anexar as capturas existentes e usar o checklist local como resumo do material entregue.

## Estrutura do projeto

```text
.
├── datasets/
│   └── bug_to_user_story.jsonl
├── prompts/
│   ├── bug_to_user_story_v1.yml
│   └── bug_to_user_story_v2.yml
├── src/
│   ├── evaluate.py
│   ├── metrics.py
│   ├── pull_prompts.py
│   ├── push_prompts.py
│   └── utils.py
├── tests/
│   └── test_prompts.py
├── requirements.txt
└── README.md
```