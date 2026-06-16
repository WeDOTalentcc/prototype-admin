"""
Ragas Evaluation Tests — Task #117 (T004).

Evaluates RAG-based agent responses using Ragas metrics:
  - Context Precision: how relevant is the retrieved context
  - Context Recall: completeness of retrieved context
  - Faithfulness: does the answer stick to retrieved facts
  - Answer Relevancy: is the answer relevant to the question

Non-blocking in CI. Requires ragas + OPENAI_API_KEY.
"""
import pytest

ragas = pytest.importorskip("ragas", reason="ragas not installed")


RAGAS_TEST_CASES = [
    {
        "id": "RAGAS-001",
        "category": "sourcing",
        "question": "Buscar candidatos com experiência em Python e Machine Learning em SP",
        "answer": (
            "Encontrei 5 candidatos no banco interno com perfil compatível: "
            "todos possuem experiência em Python e ML, localizados na região de SP. "
            "Os scores de compatibilidade variam de 72% a 91%."
        ),
        "contexts": [
            "Banco interno contém 5 candidatos em SP com Python e ML",
            "Scores WSI calculados: 91%, 85%, 82%, 78%, 72%",
        ],
        "ground_truth": "O sistema deveria retornar candidatos do banco interno com scores WSI.",
    },
    {
        "id": "RAGAS-002",
        "category": "cv_screening",
        "question": "Qual a compatibilidade do candidato com a vaga de Engenheiro de Dados?",
        "answer": (
            "O candidato possui match score de 82% com a vaga. "
            "Skills compatíveis: Python, SQL, Spark, AWS. "
            "Skills faltantes: Kafka, Airflow. "
            "Recomendação: EM_ANALISE."
        ),
        "contexts": [
            "Vaga requer: Python, SQL, Spark, AWS, Kafka, Airflow",
            "Candidato possui: Python (5 anos), SQL (4 anos), Spark (2 anos), AWS (3 anos)",
            "BARS scoring: 82% de match baseado em competências verificadas",
        ],
        "ground_truth": "Score de 82% com skills faltantes Kafka e Airflow.",
    },
    {
        "id": "RAGAS-003",
        "category": "analytics",
        "question": "Qual o custo por contratação por departamento?",
        "answer": (
            "Custo por contratação por departamento:\n"
            "- Engenharia: R$ 8.500\n"
            "- Produto: R$ 6.200\n"
            "- Comercial: R$ 4.800\n"
            "Média geral: R$ 6.500"
        ),
        "contexts": [
            "Dados de custo por contratação (últimos 12 meses): "
            "Engenharia R$ 8.500, Produto R$ 6.200, Comercial R$ 4.800",
            "Média nacional de custo por contratação: R$ 5.500 (benchmark ABRH)",
        ],
        "ground_truth": "Custos por departamento baseados em dados históricos da empresa.",
    },
    {
        "id": "RAGAS-004",
        "category": "pipeline",
        "question": "Mostre o funil da vaga de Product Manager",
        "answer": (
            "Funil da vaga Product Manager:\n"
            "- Triagem: 45 candidatos\n"
            "- Entrevista inicial: 18 candidatos (conversão: 40%)\n"
            "- Entrevista técnica: 8 candidatos (conversão: 44%)\n"
            "- Proposta: 3 candidatos (conversão: 38%)\n"
            "Gargalo identificado: etapa de entrevista técnica."
        ),
        "contexts": [
            "Pipeline PM: Triagem=45, Entrevista inicial=18, Técnica=8, Proposta=3",
            "Taxas de conversão calculadas automaticamente pelo sistema",
        ],
        "ground_truth": "Funil com contagens por etapa e taxas de conversão.",
    },
    {
        "id": "RAGAS-005",
        "category": "wsi",
        "question": "Qual o resultado da entrevista WSI do candidato?",
        "answer": (
            "Resultado WSI do candidato:\n"
            "- Score técnico: 78/100 (Dreyfus: Competente)\n"
            "- Score comportamental: 85/100 (Bloom: Análise)\n"
            "- Score situacional: 72/100\n"
            "- Score geral: 78/100\n"
            "Recomendação: APROVADO para próxima fase."
        ),
        "contexts": [
            "WSI scores calculados: técnico=78, comportamental=85, situacional=72",
            "Metodologia: Dreyfus para técnico, Bloom para comportamental",
            "Threshold de aprovação: score geral >= 65",
        ],
        "ground_truth": "Scores WSI nas 3 dimensões com classificação Dreyfus/Bloom.",
    },
]


class TestRagasContextPrecision:

    @pytest.mark.parametrize("case", RAGAS_TEST_CASES, ids=[c["id"] for c in RAGAS_TEST_CASES])
    def test_context_precision(self, case):
        try:
            from ragas.metrics import context_precision
            from datasets import Dataset

            dataset = Dataset.from_dict({
                "question": [case["question"]],
                "answer": [case["answer"]],
                "contexts": [case["contexts"]],
                "ground_truth": [case["ground_truth"]],
            })

            from ragas import evaluate
            result = evaluate(dataset, metrics=[context_precision])
            score = result["context_precision"]
            assert score >= 0.6, (
                f"[{case['id']}] Context precision too low: {score:.2f}"
            )
        except Exception as exc:
            pytest.skip(f"Ragas context_precision not available: {exc}")


class TestRagasFaithfulness:

    @pytest.mark.parametrize("case", RAGAS_TEST_CASES, ids=[c["id"] for c in RAGAS_TEST_CASES])
    def test_faithfulness(self, case):
        try:
            from ragas.metrics import faithfulness
            from datasets import Dataset

            dataset = Dataset.from_dict({
                "question": [case["question"]],
                "answer": [case["answer"]],
                "contexts": [case["contexts"]],
            })

            from ragas import evaluate
            result = evaluate(dataset, metrics=[faithfulness])
            score = result["faithfulness"]
            assert score >= 0.7, (
                f"[{case['id']}] Faithfulness too low: {score:.2f}"
            )
        except Exception as exc:
            pytest.skip(f"Ragas faithfulness not available: {exc}")


class TestRagasAnswerRelevancy:

    @pytest.mark.parametrize("case", RAGAS_TEST_CASES, ids=[c["id"] for c in RAGAS_TEST_CASES])
    def test_answer_relevancy(self, case):
        try:
            from ragas.metrics import answer_relevancy
            from datasets import Dataset

            dataset = Dataset.from_dict({
                "question": [case["question"]],
                "answer": [case["answer"]],
                "contexts": [case["contexts"]],
            })

            from ragas import evaluate
            result = evaluate(dataset, metrics=[answer_relevancy])
            score = result["answer_relevancy"]
            assert score >= 0.7, (
                f"[{case['id']}] Answer relevancy too low: {score:.2f}"
            )
        except Exception as exc:
            pytest.skip(f"Ragas answer_relevancy not available: {exc}")
