"""P1-2 sensor anti-fabricação — proveniência honesta (CLAUDE.md).

O antigo ``generate_lia_metrics`` em job_vacancies/_shared.py FABRICAVA o funil
e as métricas de Performance LIA com ``random.uniform`` — violando a regra
"Proveniência honesta em saídas de IA". Foi removido em favor de
``JobVacancyCRUDRepository.aggregate_list_metrics`` (agregação real de
vacancy_candidates + wsi_sessions + interviews).

Este sensor (computacional, barato) falha se o random voltar a aparecer no
módulo de helpers das vagas, ou se a função fabricadora for reintroduzida.
"""
import pathlib

_SHARED = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "api" / "v1" / "job_vacancies" / "_shared.py"
)


def test_shared_has_no_random_fabrication():
    src = _SHARED.read_text(encoding="utf-8")
    assert "import random" not in src, (
        "_shared.py reintroduziu 'import random' — métricas de vaga devem vir de "
        "agregação real (aggregate_list_metrics), nunca de random.uniform. "
        "Ver regra 'Proveniência honesta' no CLAUDE.md."
    )
    assert "random.uniform" not in src, (
        "_shared.py reintroduziu 'random.uniform' — proibido (fabricação de métricas)."
    )


def test_generate_lia_metrics_is_gone():
    src = _SHARED.read_text(encoding="utf-8")
    assert "def generate_lia_metrics" not in src, (
        "generate_lia_metrics foi reintroduzido — use "
        "JobVacancyCRUDRepository.aggregate_list_metrics (agregação real)."
    )
    # Não deve mais ser importável do pacote
    import app.api.v1.job_vacancies as pkg
    assert not hasattr(pkg, "generate_lia_metrics"), (
        "generate_lia_metrics ainda é exportado pelo pacote job_vacancies."
    )
