"""
P3-A — Testes: Fallback LLM no KanbanReActAgent

NOTA: Os testes desta suite testavam o bloco try/except P3-A em _process_react_loop()
que foi removido durante a migração para LangGraph nativo. O KanbanReActAgent agora
usa create_react_agent do LangGraph diretamente (sem _process_react_loop).

O comportamento de fallback de LLM agora é responsabilidade da configuração do
LangGraph e do modelo configurado, não de um loop ReAct legado.
"""
import pytest


pytestmark = pytest.mark.skip(
    reason="Testa _process_react_loop legado removido na migração LangGraph (Task #123)"
)


def test_placeholder():
    """Placeholder para evitar erros de coleta de testes vazios."""
    pass
