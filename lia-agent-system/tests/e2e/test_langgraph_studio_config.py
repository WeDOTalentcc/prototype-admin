"""
Validação do arquivo langgraph.json para LangGraph Studio.

Garante que a configuração está correta e que os módulos referenciados existem,
antes que o Studio seja usado em produção.

Cobertura (Camada 2 — Validação de Config):
  - langgraph.json existe no root do projeto
  - JSON é sintaxicamente válido
  - Chave "graphs" está presente
  - 3 grafos esperados estão configurados
  - Cada grafo usa formato "module.path:attribute"
  - Os arquivos Python referenciados existem em disco
  - A chave "env" aponta para arquivo .env existente
  - Não há grafos duplicados
"""
import json
import os
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "../..")
LANGGRAPH_JSON_PATH = os.path.join(PROJECT_ROOT, "langgraph.json")

EXPECTED_GRAPHS = {
    "wizard_graph",
    "wsi_interview_graph",
    "interview_graph",
}

# Mapeamento esperado: nome → (módulo_relativo, atributo)
EXPECTED_GRAPH_MODULES = {
    "wizard_graph": (
        "app/domains/job_management/agents/wizard_react_agent.py",
        "WizardReActAgent",
    ),
    "wsi_interview_graph": (
        "app/domains/cv_screening/agents/wsi_interview_graph.py",
        "wsi_interview_graph",
    ),
    "interview_graph": (
        "app/domains/interview_scheduling/agents/interview_graph.py",
        "interview_graph",
    ),
}


def _load_config() -> dict:
    with open(LANGGRAPH_JSON_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Existência e Sintaxe
# ---------------------------------------------------------------------------

class TestLangGraphJsonExists:

    def test_langgraph_json_file_exists(self):
        """langgraph.json deve existir no root do projeto."""
        assert os.path.isfile(LANGGRAPH_JSON_PATH), (
            f"langgraph.json não encontrado em: {LANGGRAPH_JSON_PATH}"
        )

    def test_langgraph_json_is_valid_json(self):
        """langgraph.json deve ser JSON válido."""
        try:
            config = _load_config()
            assert isinstance(config, dict)
        except json.JSONDecodeError as e:
            pytest.fail(f"langgraph.json não é JSON válido: {e}")

    def test_langgraph_json_has_graphs_key(self):
        """langgraph.json deve ter a chave 'graphs'."""
        config = _load_config()
        assert "graphs" in config, "Chave 'graphs' não encontrada em langgraph.json"

    def test_langgraph_json_graphs_is_dict(self):
        """'graphs' deve ser um dicionário."""
        config = _load_config()
        assert isinstance(config["graphs"], dict), "'graphs' deve ser um dict"


# ---------------------------------------------------------------------------
# Grafos Esperados
# ---------------------------------------------------------------------------

class TestLangGraphExpectedGraphs:

    def test_has_exactly_three_graphs(self):
        """langgraph.json deve ter exatamente 3 grafos configurados."""
        config = _load_config()
        graphs = config["graphs"]
        assert len(graphs) == 3, (
            f"Esperado 3 grafos, encontrado {len(graphs)}: {list(graphs.keys())}"
        )

    def test_wizard_graph_configured(self):
        """wizard_graph deve estar em langgraph.json."""
        config = _load_config()
        assert "wizard_graph" in config["graphs"], "wizard_graph não encontrado"

    def test_wsi_interview_graph_configured(self):
        """wsi_interview_graph deve estar em langgraph.json."""
        config = _load_config()
        assert "wsi_interview_graph" in config["graphs"], "wsi_interview_graph não encontrado"

    def test_interview_graph_configured(self):
        """interview_graph deve estar em langgraph.json."""
        config = _load_config()
        assert "interview_graph" in config["graphs"], "interview_graph não encontrado"

    def test_no_duplicate_graph_values(self):
        """Nenhum grafo deve apontar para o mesmo módulo:atributo."""
        config = _load_config()
        values = list(config["graphs"].values())
        assert len(values) == len(set(values)), "Grafos duplicados detectados em langgraph.json"


# ---------------------------------------------------------------------------
# Formato module:attribute
# ---------------------------------------------------------------------------

class TestLangGraphModuleFormat:

    @pytest.mark.parametrize("graph_name", list(EXPECTED_GRAPHS))
    def test_graph_value_has_colon_separator(self, graph_name):
        """Cada grafo deve usar formato 'module/path.py:attribute'."""
        config = _load_config()
        value = config["graphs"].get(graph_name, "")
        assert ":" in value, (
            f"Grafo '{graph_name}' não usa formato 'module:attribute'. Valor: '{value}'"
        )

    @pytest.mark.parametrize("graph_name", list(EXPECTED_GRAPHS))
    def test_graph_attribute_not_empty(self, graph_name):
        """O atributo (parte após ':') não deve ser vazio."""
        config = _load_config()
        value = config["graphs"].get(graph_name, "")
        if ":" in value:
            _, attr = value.rsplit(":", 1)
            assert attr.strip(), f"Atributo vazio para grafo '{graph_name}'"


# ---------------------------------------------------------------------------
# Arquivos Python existem
# ---------------------------------------------------------------------------

class TestLangGraphFileExists:

    @pytest.mark.parametrize("graph_name,expected", list(EXPECTED_GRAPH_MODULES.items()))
    def test_graph_python_file_exists(self, graph_name, expected):
        """O arquivo Python do grafo deve existir em disco."""
        rel_path, attr = expected
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        assert os.path.isfile(full_path), (
            f"Arquivo do grafo '{graph_name}' não encontrado: {full_path}"
        )

    @pytest.mark.parametrize("graph_name,expected", list(EXPECTED_GRAPH_MODULES.items()))
    def test_graph_path_in_config_matches_expected(self, graph_name, expected):
        """O caminho em langgraph.json deve corresponder ao arquivo esperado."""
        config = _load_config()
        rel_path, attr = expected
        configured_value = config["graphs"].get(graph_name, "")
        # O path configurado deve conter o arquivo esperado
        assert rel_path in configured_value, (
            f"Grafo '{graph_name}' configurado como '{configured_value}', "
            f"esperado conter '{rel_path}'"
        )

    @pytest.mark.parametrize("graph_name,expected", list(EXPECTED_GRAPH_MODULES.items()))
    def test_graph_attribute_matches_expected(self, graph_name, expected):
        """O atributo em langgraph.json deve corresponder ao esperado."""
        config = _load_config()
        _, attr = expected
        configured_value = config["graphs"].get(graph_name, "")
        if ":" in configured_value:
            _, configured_attr = configured_value.rsplit(":", 1)
            assert configured_attr == attr, (
                f"Atributo de '{graph_name}' é '{configured_attr}', esperado '{attr}'"
            )


# ---------------------------------------------------------------------------
# Env file
# ---------------------------------------------------------------------------

class TestLangGraphEnvConfig:

    def test_env_key_present(self):
        """langgraph.json deve ter chave 'env'."""
        config = _load_config()
        assert "env" in config, "Chave 'env' não encontrada em langgraph.json"

    def test_env_file_exists(self):
        """O arquivo .env referenciado deve existir."""
        config = _load_config()
        env_value = config.get("env", "")
        if env_value:
            env_path = os.path.join(PROJECT_ROOT, env_value)
            assert os.path.isfile(env_path), (
                f"Arquivo .env '{env_value}' referenciado em langgraph.json não existe: {env_path}"
            )

    def test_dependencies_key_present(self):
        """langgraph.json deve ter chave 'dependencies'."""
        config = _load_config()
        assert "dependencies" in config, "Chave 'dependencies' não encontrada"

    def test_dependencies_includes_current_dir(self):
        """'dependencies' deve incluir '.' (dependência local)."""
        config = _load_config()
        deps = config.get("dependencies", [])
        assert "." in deps, f"'.' não encontrado em dependencies: {deps}"
