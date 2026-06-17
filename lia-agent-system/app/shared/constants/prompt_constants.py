"""
Prompt constants shared across orchestrator services.

Centralizes hardcoded strings used in structured intent addenda
so they can be updated in one place (R-039).
"""

# R-039: Salary placeholder used in salary_benchmark intent addenda (C-06 rule)
SALARY_BENCHMARK_PLACEHOLDER = "R$ XX.XXX - R$ XX.XXX mensais (CLT)"

# R-039: Full salary output rule addendum (C-06) — shared by Orchestrator v1 and FallbackReActService
SALARY_BENCHMARK_ADDENDUM = (
    "\n\nRegra de saída salarial (C-06): sempre inclua faixas salariais no formato "
    f"{SALARY_BENCHMARK_PLACEHOLDER}. Estruture a resposta com:\n"
    "- Faixa mínima: R$ X.XXX\n"
    "- Faixa máxima: R$ X.XXX\n"
    "- Mediana: R$ X.XXX\n"
    "Use ponto como separador de milhar (ex: R$ 12.000)."
)
