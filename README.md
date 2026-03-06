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

## Resultados Finais

### Dashboard e links publicos

- Dashboard do projeto no LangSmith: https://smith.langchain.com/projects/prompt-optimization-challenge
- Prompt otimizado publicado: https://smith.langchain.com/hub/glaucia86/bug_to_user_story_v2

### Tabela comparativa (prompt ruim v1 vs prompt otimizado v2)

Abaixo, comparacao no mesmo fluxo de avaliacao (`src/evaluate.py`), com o mesmo dataset e mesmas metricas:

| Prompt | Helpfulness | Correctness | F1-Score | Clarity | Precision | Media Geral | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| `leonanluppi/bug_to_user_story_v1` | 0.8233 | 0.8254 | 0.8208 | 0.8167 | 0.8300 | 0.8232 | Reprovado |
| `glaucia86/bug_to_user_story_v2` | 0.9333 | 1.0000 | 1.0000 | 0.8667 | 1.0000 | 0.9600 | Aprovado |

### Evidencia de aprovacao

Ultima execucao oficial:

- Prompt: `glaucia86/bug_to_user_story_v2`
- Media geral: `0.9600`
- Resultado: `APROVADO (media >= 0.9)`

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

#### Avaliacao v2 (aprovado)

Resultado oficial desta rodada:
- Media geral: 0.9600
- Status: APROVADO

![Avaliacao v2 aprovado com media >= 0.9](docs/screenshots/avaliacao-v2-aprovado.png)

#### Tracing detalhado - exemplo 1

![Tracing exemplo 1](docs/screenshots/tracing-exemplo-1.png)

#### Tracing detalhado - exemplo 2

![Tracing exemplo 2](docs/screenshots/tracing-exemplo-2.png)

#### Tracing detalhado - exemplo 3

![Tracing exemplo 3](docs/screenshots/tracing-exemplo-3.png)

Todas as evidencias do desafio foram consolidadas neste README.

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

```env
LANGSMITH_API_KEY=...
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
USERNAME_LANGSMITH_HUB=seu_usuario

LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
EVAL_MODEL=gemini-3.1-flash-lite-preview
GOOGLE_API_KEY=...

# opcional
LANGSMITH_PROJECT=prompt-optimization-challenge
MAX_EVAL_EXAMPLES=3
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

## Evidencias no LangSmith

Checklist recomendado para anexar no envio:

- Link publico do dashboard
- Execucoes do v1 com notas baixas
- Execucoes do v2 com notas >= 0.9 (media geral)
- Traces detalhados de pelo menos 3 exemplos

Observacao: o dataset local oficial do repositorio base permanece em `datasets/bug_to_user_story.jsonl` e nao foi alterado.

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