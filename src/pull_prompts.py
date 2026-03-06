"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

REMOTE_PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
LOCAL_OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"

def extract_message_template(message) -> str:
    """
    Extrai o texto/template de uma mensagem do LangChain de forma tolerante
    Isso existe porque a estrutura interna da mensagem pode variar de acordo
    com a versão do pacote e com o tipo de mensagem (ex: SystemMessage, HumanMessage, etc.)
    """
    prompt_obj = getattr(message, "prompt", None)
    if prompt_obj is not None:
        template = getattr(prompt_obj, "template", None)
        if isinstance(template, str):
            return template
    
    template = getattr(message, "template", None)
    if isinstance(template, str):
        return template

    return str(message)

def extract_prompts_from_template(prompt_obj) -> dict:
    """
    Extrai system_prompt e user_prompt do objeto retornado por hub.pull()
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_obj, "messages", None)
    if messages is None:
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }

    for message in messages:
        class_name = message.__class__.__name__.lower()
        content = extract_message_template(message).strip()
        
        if "system" in class_name and not system_prompt:
            system_prompt = content
        elif ("human" in class_name or "user" in class_name) and not user_prompt:
            user_prompt = content
            
    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt
    }
    
def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt remoto e salva em YAML local.

    Returns:
        True se sucesso, False caso contrário
    """
    print_section_header("PULL DO PROMPT DO LANGSMITH")
    
    required_vars = [
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
    ]
    
    if not check_env_vars(required_vars):
        return False
    
    try:
        print(f"Buscando prompt remoto: {REMOTE_PROMPT_NAME}")
        prompt = hub.pull(REMOTE_PROMPT_NAME)
        
        if prompt is None:
            print("❌ Não foi possível carregar o prompt remoto.")
            return False
        
        extracted = extract_prompts_from_template(prompt)
        
        if not extracted["system_prompt"]:
            print("❌ Não foi possível extrair o system_prompt.")
            return False
        
        yaml_data = {
           "bug_to_user_story_v1": {
                "description": "Prompt inicial importado do LangSmith Prompt Hub",
                "system_prompt": extracted["system_prompt"],
                "user_prompt": extracted["user_prompt"] or "{bug_report}",
                "version": "v1",
                "source": REMOTE_PROMPT_NAME,
                "tags": [
                    "bug-analysis",
                    "user-story",
                    "langsmith-import",
                ],
            } 
        }
        
        saved = save_yaml(yaml_data, LOCAL_OUTPUT_PATH)
        if not saved:
            print("❌ Falha ao salvar o prompt localmente.")
            return False
        
        print(f"✅ Prompt salvo localmente em: {LOCAL_OUTPUT_PATH}")
        return True
    
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return False

def main():
    """Função principal"""
    success = pull_prompts_from_langsmith()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
