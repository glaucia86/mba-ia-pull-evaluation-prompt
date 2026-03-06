"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


@pytest.fixture(scope="module")
def prompt_data():
    data = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    return prompt_data.get("system_prompt", "")

class TestPrompts:
    def test_prompt_has_system_prompt(self, system_prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert isinstance(system_prompt, str)
        assert system_prompt.strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert "você é" in system_prompt.lower(), "Prompt não define persona explicitamente"
        assert re.search(r"product manager|business analyst", system_prompt, re.IGNORECASE), (
            "Prompt não contém papel esperado (Product Manager / Business Analyst)"
        )

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        assert "como [tipo de usuário]" in system_prompt.lower(), (
            "Prompt não define formato padrão de User Story"
        )
        assert "critérios de aceitação" in system_prompt.lower(), (
            "Prompt não exige seção de critérios de aceitação"
        )

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        case_markers = re.findall(r"CASO CR[IÍ]TICO", system_prompt, flags=re.IGNORECASE)
        assert len(case_markers) >= 2, "Prompt não contém exemplos suficientes (few-shot)"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = yaml.dump(prompt_data, allow_unicode=True)
        assert "[TODO]" not in full_text
        assert re.search(r"\bTODO\b", full_text, flags=re.IGNORECASE) is None

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques", [])
        assert isinstance(techniques, list), "Campo 'techniques' deve ser uma lista"
        assert len(techniques) >= 2, "Mínimo de 2 técnicas requeridas"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])