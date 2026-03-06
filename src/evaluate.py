"""
Script para avaliar prompts otimizados.

Este script:
1. Carrega dataset de avaliação de arquivo .jsonl
2. Cria/atualiza dataset no LangSmith
3. Puxa prompt otimizado do LangSmith Hub
4. Executa prompt contra o dataset
5. Calcula métricas atuais do template
6. Exibe resumo no terminal
"""

import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import (
    check_env_vars,
    format_score,
    print_section_header,
    get_llm as get_configured_llm,
    invoke_with_retry,
)
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()

def get_llm():
    return get_configured_llm(temperature=0)

def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    example = json.loads(line)
                    examples.append(example)

        return examples

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {jsonl_path}")
        print("\nCertifique-se de que o arquivo datasets/bug_to_user_story.jsonl existe.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSONL: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> str:
    print(f"Criando dataset de avaliação: {dataset_name}...")

    examples = load_dataset_from_jsonl(jsonl_path)

    if not examples:
        print("❌ Nenhum exemplo carregado do arquivo .jsonl")
        return dataset_name

    print(f"   ✓ Carregados {len(examples)} exemplos do arquivo {jsonl_path}")

    try:
        datasets = client.list_datasets(dataset_name=dataset_name)
        existing_dataset = None

        for ds in datasets:
            if ds.name == dataset_name:
                existing_dataset = ds
                break

        if existing_dataset:
            print(f"   ✓ Dataset '{dataset_name}' já existe, usando existente")
            return dataset_name

        dataset = client.create_dataset(dataset_name=dataset_name)

        for example in examples:
            client.create_example(
                dataset_id=dataset.id,
                inputs=example["inputs"],
                outputs=example["outputs"],
            )

        print(f"   ✓ Dataset criado com {len(examples)} exemplos")
        return dataset_name

    except Exception as e:
        print(f"   ⚠️ Erro ao criar dataset: {e}")
        return dataset_name

def pull_prompt_from_langsmith(prompt_name: str) -> ChatPromptTemplate:
    try:
        print(f"   Puxando prompt do LangSmith Hub: {prompt_name}")
        prompt = hub.pull(prompt_name)
        print("   ✓ Prompt carregado com sucesso")
        return prompt

    except Exception as e:
        error_msg = str(e).lower()

        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível carregar o prompt '{prompt_name}'")
        print(f"{'=' * 70}\n")

        if "not found" in error_msg or "404" in error_msg:
            print("⚠️ O prompt não foi encontrado no LangSmith Hub.\n")
            print("AÇÕES NECESSÁRIAS:")
            print("1. Verifique se você já fez push do prompt otimizado:")
            print("   python src/push_prompts.py")
            print()
            print("2. Confirme se o prompt foi publicado com sucesso em:")
            print("   https://smith.langchain.com/prompts")
            print()
            print(f"3. Certifique-se de que o nome do prompt está correto: '{prompt_name}'")
            print()
            print("4. Se você alterou o prompt no YAML, refaça o push:")
            print("   python src/push_prompts.py")
        else:
            print(f"Erro técnico: {e}\n")
            print("Verifique:")
            print("- LANGSMITH_API_KEY está configurada corretamente no .env")
            print("- Você tem acesso ao workspace do LangSmith")
            print("- Sua conexão com a internet está funcionando")

        print(f"\n{'=' * 70}\n")
        raise


def evaluate_prompt_on_example(
    prompt_template: ChatPromptTemplate,
    example: Any,
    llm: Any,
) -> Dict[str, Any]:
    try:
        inputs = example.inputs if hasattr(example, "inputs") else {}
        outputs = example.outputs if hasattr(example, "outputs") else {}

        chain = prompt_template | llm
        response = invoke_with_retry(
            chain,
            inputs,
            operation_name="geracao de resposta",
        )
        answer = response.content

        reference = outputs.get("reference", "") if isinstance(outputs, dict) else ""

        if isinstance(inputs, dict):
            question = inputs.get("question", inputs.get("bug_report", inputs.get("pr_title", "N/A")))
        else:
            question = "N/A"

        return {
            "answer": answer,
            "reference": reference,
            "question": question,
        }

    except Exception as e:
        print(f"      ⚠️ Erro ao avaliar exemplo: {e}")
        return {
            "answer": "",
            "reference": "",
            "question": "",
        }


def evaluate_prompt(
    prompt_name: str,
    dataset_name: str,
    client: Client,
) -> Dict[str, float]:
    print(f"\n🔍 Avaliando: {prompt_name}")

    try:
        prompt_template = pull_prompt_from_langsmith(prompt_name)

        examples = list(client.list_examples(dataset_name=dataset_name))
        print(f"   Dataset: {len(examples)} exemplos")

        llm = get_llm()

        f1_scores = []
        clarity_scores = []
        precision_scores = []

        print("   Avaliando exemplos...")

        MAX_EXAMPLES = int(os.getenv("MAX_EVAL_EXAMPLES", "3"))
        
        for i, example in enumerate(examples[:MAX_EXAMPLES], 1):
            result = evaluate_prompt_on_example(prompt_template, example, llm)

            if result["answer"]:
                f1 = evaluate_f1_score(result["question"], result["answer"], result["reference"])
                clarity = evaluate_clarity(result["question"], result["answer"], result["reference"])
                precision = evaluate_precision(result["question"], result["answer"], result["reference"])

                f1_scores.append(f1["score"])
                clarity_scores.append(clarity["score"])
                precision_scores.append(precision["score"])

                print(
                    f"      [{i}/{min(MAX_EXAMPLES, len(examples))}] "
                    f"F1:{f1['score']:.2f} "
                    f"Clarity:{clarity['score']:.2f} "
                    f"Precision:{precision['score']:.2f}"
                )

        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.0
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0

        avg_helpfulness = (avg_clarity + avg_precision) / 2
        avg_correctness = (avg_f1 + avg_precision) / 2

        return {
            "helpfulness": round(avg_helpfulness, 4),
            "correctness": round(avg_correctness, 4),
            "f1_score": round(avg_f1, 4),
            "clarity": round(avg_clarity, 4),
            "precision": round(avg_precision, 4),
        }

    except Exception as e:
        print(f"   ❌ Erro na avaliação: {e}")
        return {
            "helpfulness": 0.0,
            "correctness": 0.0,
            "f1_score": 0.0,
            "clarity": 0.0,
            "precision": 0.0,
        }


def display_results(prompt_name: str, scores: Dict[str, float]) -> bool:
    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)

    print("\nMétricas LangSmith:")
    print(f"  - Helpfulness: {format_score(scores['helpfulness'], threshold=0.9)}")
    print(f"  - Correctness: {format_score(scores['correctness'], threshold=0.9)}")
    
    print("\nMétricas Customizadas:")
    print(f"  - F1-Score: {format_score(scores['f1_score'], threshold=0.9)}")
    print(f"  - Clarity: {format_score(scores['clarity'], threshold=0.9)}")
    print(f"  - Precision: {format_score(scores['precision'], threshold=0.9)}")

    average_score = sum(scores.values()) / len(scores)

    print("\n" + "-" * 50)
    print(f"📊 MÉDIA GERAL: {average_score:.4f}")
    print("-" * 50)

    passed = average_score >= 0.9

    if passed:
        print("\n✅ STATUS: APROVADO (média >= 0.9)")
    else:
        print("\n❌ STATUS: REPROVADO (média < 0.9)")
        print(f"⚠️ Média atual: {average_score:.4f} | Necessário: 0.9000")

    return passed


def main():
    print_section_header("AVALIAÇÃO DE PROMPTS OTIMIZADOS")

    provider = os.getenv("LLM_PROVIDER", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    eval_model = os.getenv("EVAL_MODEL", "gpt-4o")
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    print(f"Provider: {provider}")
    print(f"Modelo Principal: {llm_model}")
    print(f"Modelo de Avaliação: {eval_model}")
    print(f"Handle LangSmith Hub: {username}\n")

    required_vars = ["LANGSMITH_API_KEY", "LLM_PROVIDER", "USERNAME_LANGSMITH_HUB"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif provider in ["google", "gemini"]:
        required_vars.append("GOOGLE_API_KEY")

    if not check_env_vars(required_vars):
        return 1

    client = Client()

    project_name = (
        os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or "prompt-optimization-challenge"
    )

    jsonl_path = "datasets/bug_to_user_story.jsonl"

    if not Path(jsonl_path).exists():
        print(f"❌ Arquivo de dataset não encontrado: {jsonl_path}")
        print("\nCertifique-se de que o arquivo existe antes de continuar.")
        return 1

    dataset_name = f"{project_name}-eval"
    create_evaluation_dataset(client, dataset_name, jsonl_path)

    print("\n" + "=" * 70)
    print("PROMPT PARA AVALIAR")
    print("=" * 70)
    print("\nEste script irá puxar o prompt do LangSmith Hub.")
    print("Certifique-se de ter feito push do prompt antes de avaliar:")
    print("  python src/push_prompts.py\n")

    prompts_to_evaluate = [
        f"{username}/bug_to_user_story_v2",
    ]

    all_passed = True
    evaluated_count = 0
    results_summary = []

    for prompt_name in prompts_to_evaluate:
        evaluated_count += 1

        try:
            scores = evaluate_prompt(prompt_name, dataset_name, client)

            passed = display_results(prompt_name, scores)
            all_passed = all_passed and passed

            results_summary.append(
                {
                    "prompt": prompt_name,
                    "scores": scores,
                    "passed": passed,
                }
            )

        except Exception as e:
            print(f"\n❌ Falha ao avaliar '{prompt_name}': {e}")
            all_passed = False

            results_summary.append(
                {
                    "prompt": prompt_name,
                    "scores": {
                        "helpfulness": 0.0,
                        "correctness": 0.0,
                        "f1_score": 0.0,
                        "clarity": 0.0,
                        "precision": 0.0,
                    },
                    "passed": False,
                }
            )

    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50 + "\n")

    if evaluated_count == 0:
        print("⚠️ Nenhum prompt foi avaliado")
        return 1

    print(f"Prompts avaliados: {evaluated_count}")
    print(f"Aprovados: {sum(1 for r in results_summary if r['passed'])}")
    print(f"Reprovados: {sum(1 for r in results_summary if not r['passed'])}\n")

    if all_passed:
        print("✅ Todos os prompts atingiram média >= 0.9!")
        print(f"\n✓ Confira os resultados em:")
        print(f"  https://smith.langchain.com/projects/{project_name}")
        print("\nPróximos passos:")
        print("1. Implementar e rodar os testes com pytest")
        print("2. Documentar o processo no README.md")
        print("3. Fazer commit e push para o GitHub")
        return 0

    print("⚠️ Alguns prompts não atingiram média >= 0.9")
    print("\nPróximos passos:")
    print("1. Refatorar o prompt com score baixo")
    print("2. Fazer push novamente: python src/push_prompts.py")
    print("3. Executar: python src/evaluate.py novamente")
    return 1


if __name__ == "__main__":
    sys.exit(main())