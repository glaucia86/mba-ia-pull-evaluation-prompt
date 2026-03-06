"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

LOCAL_PROMPT_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"

def build_prompt_from_yaml(prompt_data: dict) -> ChatPromptTemplate:
    """
    Constrói um ChatPromptTemplate a partir dos dados do YAML.

    Args:
        prompt_data: Dados do prompt extraídos do YAML

    Returns:
        ChatPromptTemplate construído
    """
    system_prompt = prompt_data.get("system_prompt", "")
    user_prompt = prompt_data.get("user_prompt", "").strip()
    
    if not system_prompt:
        raise ValueError("system_prompt não encontrado ou vazio no YAML.")
    
    if not user_prompt:
        raise ValueError("user_prompt não encontrado ou vazio no YAML.")
    
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

def push_prompt_to_langsmith() -> bool:
    """
    Lê o YAML local e publica o prompt no LangSmith Hub.

    Returns:
        True se sucesso, False caso contrário
    """
    
    print_section_header("PUSH DO PROMPT PARA O LANGSMITH")
    
    required_vars = [
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
        "USERNAME_LANGSMITH_HUB",
    ]
    
    if not check_env_vars(required_vars):
        return False
    
    username = os.getenv("USERNAME_LANGSMITH_HUB") or ""
    
    yaml_data = load_yaml(LOCAL_PROMPT_PATH)
    if not yaml_data:
        print(f"❌ Não foi possível carregar o arquivo YAML: {LOCAL_PROMPT_PATH}")
        return False
    
    prompt_block = yaml_data.get(PROMPT_KEY)
    if not prompt_block:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada no YAML.")
        return False

    try:
        prompt_template = build_prompt_from_yaml(prompt_block)
        full_prompt_name = f"{username}/{PROMPT_KEY}"
        
        print(f"Publicando prompt para o LangSmith Hub: {full_prompt_name}")
        
        hub.push(
            repo_full_name=full_prompt_name,
            object=prompt_template,
            new_repo_is_public=True,
        )
        
        print(f"✅ Prompt publicado com sucesso, em: {full_prompt_name}!")
        return True
    
    except Exception as e:
        error_text = str(e)

        # Idempotência: se não há mudanças para commitar no Hub, tratamos como sucesso.
        if "Nothing to commit" in error_text:
            print("INFO: Prompt sem alteracoes desde o ultimo commit no LangSmith Hub.")
            print("OK: Repositorio remoto ja esta atualizado.")
            return True

        print(f"❌ Erro ao publicar o prompt: {e}")
        return False

def main():
    """Função principal"""
    success = push_prompt_to_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
