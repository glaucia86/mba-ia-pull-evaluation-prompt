"""
Funções auxiliares para o projeto de otimização de prompts.
"""

import os
import yaml
import json
import time
import random
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

load_dotenv()


_LAST_REQUEST_TS = 0.0


def _get_env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _get_env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def _get_min_request_interval_seconds() -> float:
    """
    Retorna intervalo mínimo entre chamadas ao LLM.

    Padrão:
    - Google/Gemini: ~4.2s (≈14 req/min) para ficar abaixo do limite free de 15 req/min
    - OpenAI e outros: 0s

    Pode ser sobrescrito por LLM_MIN_REQUEST_INTERVAL_SECONDS no .env.
    """
    configured = os.getenv("LLM_MIN_REQUEST_INTERVAL_SECONDS")
    if configured is not None:
        return max(0.0, _get_env_float("LLM_MIN_REQUEST_INTERVAL_SECONDS", 0.0))

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider in {"google", "gemini"}:
        return 4.2

    return 0.0


def _apply_request_spacing() -> None:
    """Aplica espaçamento mínimo entre chamadas para evitar rajadas e 429."""
    global _LAST_REQUEST_TS

    min_interval = _get_min_request_interval_seconds()
    if min_interval <= 0:
        return

    now = time.monotonic()
    if _LAST_REQUEST_TS > 0:
        elapsed = now - _LAST_REQUEST_TS
        wait_seconds = min_interval - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    _LAST_REQUEST_TS = time.monotonic()


def _extract_status_code(error: Exception) -> Optional[int]:
    response = getattr(error, "response", None)
    if response is None:
        return None

    status_code = getattr(response, "status_code", None)
    return status_code if isinstance(status_code, int) else None


def _extract_retry_after_seconds(error: Exception) -> Optional[float]:
    response = getattr(error, "response", None)
    if response is None:
        return None

    headers = getattr(response, "headers", None)
    if not headers:
        return None

    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after is None:
        return None

    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return None


def is_retryable_llm_error(error: Exception) -> bool:
    """
    Identifica erros transitórios/retryable em providers de LLM.

    Exemplos: 429 (rate limit/quota), 5xx, timeout, indisponibilidade temporária.
    """
    retryable_status_codes = {408, 409, 425, 429, 500, 502, 503, 504}
    status_code = _extract_status_code(error)
    if status_code in retryable_status_codes:
        return True

    error_text = str(error).lower()
    retryable_markers = [
        "429",
        "too many requests",
        "rate limit",
        "quota",
        "resource_exhausted",
        "temporarily unavailable",
        "service unavailable",
        "deadline exceeded",
        "timed out",
        "timeout",
        "try again later",
    ]

    return any(marker in error_text for marker in retryable_markers)


def invoke_with_retry(runnable: Any, payload: Any, operation_name: str = "chamada ao LLM") -> Any:
    """
    Executa runnable.invoke(payload) com retry exponencial e jitter para erros transitórios.

    Variáveis de ambiente opcionais:
    - LLM_RETRY_MAX_ATTEMPTS (default: 5)
    - LLM_RETRY_INITIAL_DELAY_SECONDS (default: 2.0)
    - LLM_RETRY_BACKOFF_FACTOR (default: 2.0)
    - LLM_RETRY_MAX_DELAY_SECONDS (default: 30.0)
    - LLM_RETRY_JITTER_SECONDS (default: 0.35)
    - LLM_MIN_REQUEST_INTERVAL_SECONDS (default dinâmico por provider)
    """
    max_attempts = max(1, _get_env_int("LLM_RETRY_MAX_ATTEMPTS", 5))
    initial_delay = max(0.1, _get_env_float("LLM_RETRY_INITIAL_DELAY_SECONDS", 2.0))
    backoff_factor = max(1.0, _get_env_float("LLM_RETRY_BACKOFF_FACTOR", 2.0))
    max_delay = max(initial_delay, _get_env_float("LLM_RETRY_MAX_DELAY_SECONDS", 30.0))
    jitter = max(0.0, _get_env_float("LLM_RETRY_JITTER_SECONDS", 0.35))

    current_delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            _apply_request_spacing()
            return runnable.invoke(payload)

        except Exception as error:
            can_retry = is_retryable_llm_error(error)
            is_last_attempt = attempt >= max_attempts

            if is_last_attempt or not can_retry:
                raise

            retry_after = _extract_retry_after_seconds(error)

            if retry_after is not None:
                sleep_seconds = min(max_delay, retry_after)
            else:
                sleep_seconds = min(max_delay, current_delay + random.uniform(0.0, jitter))

            print(
                f"WARNING: {operation_name} falhou (tentativa {attempt}/{max_attempts}) "
                f"com erro temporario. Nova tentativa em {sleep_seconds:.1f}s."
            )

            time.sleep(sleep_seconds)
            current_delay = min(max_delay, current_delay * backoff_factor)


def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Carrega arquivo YAML.

    Args:
        file_path: Caminho do arquivo YAML

    Returns:
        Dicionário com conteúdo do YAML ou None se erro
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Erro ao parsear YAML: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return None


def save_yaml(data: Dict[str, Any], file_path: str) -> bool:
    """
    Salva dados em arquivo YAML.

    Args:
        data: Dados para salvar
        file_path: Caminho do arquivo de saída

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        output_file = Path(file_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)

        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return False


def check_env_vars(required_vars: list) -> bool:
    """
    Verifica se variáveis de ambiente obrigatórias estão configuradas.

    Args:
        required_vars: Lista de variáveis obrigatórias

    Returns:
        True se todas configuradas, False caso contrário
    """
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Variáveis de ambiente faltando:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigure-as no arquivo .env antes de continuar.")
        return False

    return True


def format_score(score: float, threshold: float = 0.9) -> str:
    """
    Formata score com indicador visual de aprovação.

    Args:
        score: Score entre 0.0 e 1.0
        threshold: Limite mínimo para aprovação

    Returns:
        String formatada com score e símbolo
    """
    symbol = "✓" if score >= threshold else "✗"
    return f"{score:.2f} {symbol}"


def print_section_header(title: str, char: str = "=", width: int = 50):
    """
    Imprime cabeçalho de seção formatado.

    Args:
        title: Título da seção
        char: Caractere para a linha
        width: Largura da linha
    """
    print("\n" + char * width)
    print(title)
    print(char * width + "\n")


def validate_prompt_structure(prompt_data: Dict[str, Any]) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt.

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ['description', 'system_prompt', 'version']
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    system_prompt = prompt_data.get('system_prompt', '').strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")

    if 'TODO' in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    techniques = prompt_data.get('techniques_applied', [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Extrai JSON de uma resposta de LLM que pode conter texto adicional.

    Args:
        response_text: Texto da resposta do LLM

    Returns:
        Dicionário extraído ou None se não encontrar JSON válido
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1

        if start != -1 and end > start:
            try:
                json_str = response_text[start:end]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

    return None


def _normalize_model_name(model_name: str) -> str:
    normalized = model_name.strip().lower()
    if normalized.startswith("models/"):
        normalized = normalized.split("/", 1)[1]
    return normalized


def _is_gemma_model_name(model_name: str) -> bool:
    return _normalize_model_name(model_name).startswith("gemma")


def prepare_messages_for_model(messages: List[BaseMessage], llm: Any) -> List[BaseMessage]:
    """
    Ajusta mensagens para modelos que não aceitam instruções de sistema nativamente.

    No endpoint atual do Gemma via Google, mensagens de sistema geram erro
    "Developer instruction is not enabled...". Neste caso, convertemos
    SystemMessage para HumanMessage preservando o conteúdo.
    """
    model_name = str(getattr(llm, "model", "") or getattr(llm, "model_name", ""))
    if not _is_gemma_model_name(model_name):
        return messages

    converted_messages: List[BaseMessage] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            converted_messages.append(HumanMessage(content=message.content))
        else:
            converted_messages.append(message)

    return converted_messages


def get_llm(model: Optional[str] = None, temperature: float = 0.0):
    """
    Retorna uma instância de LLM configurada baseada no provider.

    Args:
        model: Nome do modelo (opcional, usa LLM_MODEL do .env por padrão)
        temperature: Temperatura para geração (padrão: 0.0 para determinístico)

    Returns:
        Instância de ChatOpenAI ou ChatGoogleGenerativeAI

    Raises:
        ValueError: Se provider não for suportado ou API key não configurada
    """
    provider = os.getenv('LLM_PROVIDER', 'openai').lower()
    model_name = model or os.getenv('LLM_MODEL', 'gpt-4o-mini')
    provider_max_retries = max(0, _get_env_int('LLM_PROVIDER_MAX_RETRIES', 2))
    request_timeout = max(1.0, _get_env_float('LLM_TIMEOUT_SECONDS', 120.0))

    if provider == 'openai':
        from langchain_openai import ChatOpenAI

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada no .env\n"
                "Obtenha uma chave em: https://platform.openai.com/api-keys"
            )

        openai_kwargs: Dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "api_key": SecretStr(api_key),
            "max_retries": provider_max_retries,
            "timeout": request_timeout,
        }

        return ChatOpenAI(**openai_kwargs)

    elif provider in {'google', 'gemini'}:
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY não configurada no .env\n"
                "Obtenha uma chave em: https://aistudio.google.com/app/apikey"
            )

        google_kwargs: Dict[str, Any] = {
            'model': model_name,
            'temperature': temperature,
            'max_retries': provider_max_retries,
            'timeout': request_timeout,
        }

        # Compatibilidade entre versões: alguns releases aceitam "google_api_key",
        # outros usam "api_key".
        key_field = 'google_api_key' if 'google_api_key' in ChatGoogleGenerativeAI.model_fields else 'api_key'
        google_kwargs[key_field] = api_key

        return ChatGoogleGenerativeAI(**google_kwargs)

    else:
        raise ValueError(
            f"Provider '{provider}' não suportado.\n"
            f"Use 'openai' ou 'google' na variável LLM_PROVIDER do .env"
        )


def get_eval_llm(temperature: float = 0.0):
    """
    Retorna LLM configurado especificamente para avaliação (usa EVAL_MODEL).

    Args:
        temperature: Temperatura para geração

    Returns:
        Instância de LLM configurada para avaliação
    """
    eval_model = os.getenv('EVAL_MODEL', 'gpt-4o')
    return get_llm(model=eval_model, temperature=temperature)
