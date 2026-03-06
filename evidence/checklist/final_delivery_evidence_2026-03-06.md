# Checklist de Entrega Final

Data: 2026-03-06

## Itens do repositorio

- Repositorio com implementacao completa do fluxo de pull, push e avaliacao de prompts.
- Prompt otimizado em `prompts/bug_to_user_story_v2.yml`.
- Testes automatizados em `tests/test_prompts.py`.
- README consolidando tecnicas, execucao e evidencias.

## Evidencias principais

- Dashboard do projeto no LangSmith.
- Prompt publicado no LangSmith Hub: `glaucia86/bug_to_user_story_v2`.
- Capturas locais em `docs/screenshots/`:
  - `dashboard-projeto-langsmith.png`
  - `avaliacao-v1-baixa-nota.png`
  - `avaliacao-v2-aprovado.png`
  - `avaliacao-score-baixo-0.75.png`
  - `avaliacao-score-alto-1.0.png`
  - `tracing-exemplo-1.png`
  - `tracing-exemplo-2.png`
  - `tracing-exemplo-3.png`

## Observacao sobre configuracao

- A melhor rodada documentada durante a iteracao foi obtida com modelos Gemini e esta refletida nas capturas do LangSmith.
- Revalidacoes posteriores com Gemma foram usadas como contingencia apos esgotamento da cota free do Gemini.
- Como a escolha do modelo altera a saida gerada e a avaliacao, essas rodadas posteriores nao substituem a rodada documentada principal.

## Fechamento recomendado

- Anexar links publicos do dashboard e do prompt publicado.
- Anexar ou incorporar as capturas de tela existentes.
- Usar este checklist como resumo objetivo do material entregue.