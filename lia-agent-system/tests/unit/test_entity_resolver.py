"""TDD entity resolver — match deterministico de vaga nomeada.
Fix P0 2026-06-06: threshold nao pode falhar em titulos bilingues/parenteticos."""
from app.shared.entity_resolver import _tokens, match_titles_in_message


def test_casa_diretor_juridico_apesar_da_grafia():
    jobs = [("j1", "Diretor(a) Jurídico(a)"), ("j2", "Android Developer Pleno"),
            ("j3", "Gerente de Tesouraria")]
    out = match_titles_in_message("rankeie candidatos da vaga Diretor Jurídico", jobs)
    assert out and out[0][0] == "j1"
    assert "j2" not in [i for i, _ in out]


def test_casa_titulo_bilingue_parentetico():
    # P0 real: titulo com traducao em parenteses inflava tokens (40% < 60%)
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


def test_tokens_ignora_stopwords_e_acento():
    assert _tokens("Diretor(a) Jurídico(a)") == {"diretor", "juridico"}
    assert "vaga" not in _tokens("vaga de Diretor")


def test_titulo_de_1_token_casa_exato():
    jobs = [("j1", "Recrutador")]
    assert match_titles_in_message("perfil da vaga Recrutador", jobs)[0][0] == "j1"
    assert match_titles_in_message("vaga de Designer", jobs) == []
