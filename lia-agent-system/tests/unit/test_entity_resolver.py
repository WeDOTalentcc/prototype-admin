"""TDD entity resolver — match deterministico de vaga + candidato nomeado.
Fix P0 (titulo bilingue) + Fix P1 (nome de candidato fuzzy: lowercase/typo/sem-trigger)."""
from app.shared.entity_resolver import (
    _best_fuzzy_match,
    _extract_name_query,
    _tokens,
    match_titles_in_message,
)


# ── Vagas (match por tokens) ──
def test_casa_diretor_juridico_apesar_da_grafia():
    jobs = [("j1", "Diretor(a) Jurídico(a)"), ("j2", "Android Developer Pleno"),
            ("j3", "Gerente de Tesouraria")]
    out = match_titles_in_message("rankeie candidatos da vaga Diretor Jurídico", jobs)
    assert out and out[0][0] == "j1"
    assert "j2" not in [i for i, _ in out]


def test_casa_titulo_bilingue_parentetico():
    jobs = [("j1", "Diretor(a) Jurídico(a) (Chief Legal Officer)"),
            ("j2", "Gerente de Impostos")]
    out = match_titles_in_message("temos uma vaga de diretor juridico ativa?", jobs)
    assert out and out[0][0] == "j1"
    assert "j2" not in [i for i, _ in out]


def test_nao_casa_quando_nenhum_token_bate():
    jobs = [("j1", "Diretor(a) Jurídico(a)"), ("j2", "Android Developer")]
    assert match_titles_in_message("qual o clima hoje", jobs) == []


def test_um_token_so_nao_super_casa():
    jobs = [("j1", "Diretor(a) Jurídico(a) (Chief Legal Officer)"),
            ("j2", "Diretor de Inovacao")]
    assert match_titles_in_message("abrir vaga de diretor", jobs) == []


def test_ordena_por_tokens_casados():
    jobs = [("j1", "Engenheiro de Dados"), ("j2", "Engenheiro de Dados Sênior Pleno")]
    out = match_titles_in_message("vaga engenheiro de dados senior pleno", jobs)
    assert out[0][0] == "j2"


def test_titulo_de_1_token_casa_exato():
    jobs = [("j1", "Recrutador")]
    assert match_titles_in_message("perfil da vaga Recrutador", jobs)[0][0] == "j1"
    assert match_titles_in_message("vaga de Designer", jobs) == []


# ── Candidato: extração de nome (case-insensitive, sem exigir gatilho+maiúscula) ──
def test_extract_name_apos_perfil_da():
    assert _extract_name_query("mostre o perfil da yasmim reis") == "yasmim reis"


def test_extract_name_tem_na_base():
    assert _extract_name_query("tem felipe almeida na base") == "felipe almeida"


def test_extract_name_perfil_completo():
    assert _extract_name_query("isso, quero ver o perfil completo da yasmim reis") == "yasmim reis"


def test_extract_name_sem_nome_retorna_vazio():
    assert _extract_name_query("rankeie os candidatos da vaga") == ""
    assert _extract_name_query("listar vagas ativas") == ""


# ── Candidato: match fuzzy (difflib, sem pg_trgm) ──
def test_fuzzy_typo_uma_letra_yasmim_yasmin():
    pool = [("c1", "Yasmin Reis"), ("c2", "Bruno Costa")]
    out = _best_fuzzy_match("yasmim reis", pool)
    assert out and out[0][0] == "c1"


def test_fuzzy_containment_primeiro_nome():
    pool = [("c1", "João Silva"), ("c2", "Maria Souza")]
    out = _best_fuzzy_match("joão", pool)
    assert out and out[0][0] == "c1"


def test_fuzzy_nome_completo_exato():
    pool = [("c1", "Felipe Almeida"), ("c2", "Felipe Cardoso")]
    out = _best_fuzzy_match("felipe almeida", pool)
    assert out[0][0] == "c1"


def test_fuzzy_ruido_nao_casa():
    pool = [("c1", "Yasmin Reis"), ("c2", "Bruno Costa")]
    assert _best_fuzzy_match("aberta", pool) == []


# ── Fix #2 cross-turn 2026-06-06: vaga da história via referente ("dessa vaga") ─
import pytest as _pytest_x  # noqa: E402
from app.shared.entity_resolver import (  # noqa: E402
    _has_vacancy_referent,
    resolve_named_entities,
)


def test_referente_vaga_dessa_essa_da():
    assert _has_vacancy_referent("liste os candidatos dessa vaga")
    assert _has_vacancy_referent("rankeie os melhores dessa vaga")
    assert _has_vacancy_referent("os candidatos da vaga")
    assert _has_vacancy_referent("mostre os perfis dela")


def test_nao_referente_criacao_ou_global():
    assert not _has_vacancy_referent("criar uma vaga de gerente")
    assert not _has_vacancy_referent("liste todos os candidatos")
    assert not _has_vacancy_referent("quais vagas temos abertas")


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self._rows


class _FakeDB:
    def __init__(self, jobs):
        self._jobs = jobs

    async def execute(self, stmt, params=None):
        if "job_vacancies" in str(stmt):
            return _FakeResult([{"id": i, "title": t} for i, t in self._jobs])
        return _FakeResult([])


@_pytest_x.mark.asyncio
async def test_resolve_usa_vaga_da_historia_quando_referente_sem_nome():
    db = _FakeDB([("610705ab", "Diretor(a) Jurídico(a) (Chief Legal Officer)")])
    history = "LIA: Sim! Temos a vaga Diretor(a) Jurídico(a) (Chief Legal Officer)"
    out = await resolve_named_entities(
        "liste os candidatos dessa vaga", "co1", db, history_text=history
    )
    assert out["jobs"] and out["jobs"][0][0] == "610705ab"
    assert "610705ab" in out["hint"]


@_pytest_x.mark.asyncio
async def test_resolve_nao_pega_historia_em_query_global():
    db = _FakeDB([("610705ab", "Diretor(a) Jurídico(a) (Chief Legal Officer)")])
    history = "LIA: Sim! Temos a vaga Diretor(a) Jurídico(a) (Chief Legal Officer)"
    out = await resolve_named_entities(
        "liste todos os candidatos", "co1", db, history_text=history
    )
    assert not out["jobs"]


def test_active_vacancy_contextvar_set_get_reset():
    from app.shared.entity_resolver import set_active_vacancy, get_active_vacancy
    set_active_vacancy("610705ab")
    assert get_active_vacancy() == "610705ab"
    set_active_vacancy("")
    assert get_active_vacancy() == ""
    set_active_vacancy(None)
    assert get_active_vacancy() == ""
