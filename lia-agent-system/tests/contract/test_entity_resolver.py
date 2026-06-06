"""Sensor — match determinístico de entidade (bloqueador-2). Função pura."""
from app.shared.entity_resolver import _tokens, match_titles_in_message


def test_casa_diretor_juridico_apesar_da_grafia():
    # usuario diz "Diretor Jurídico"; titulo no banco "Diretor(a) Jurídico(a)"
    jobs = [
        ("j1", "Diretor(a) Jurídico(a)"),
        ("j2", "Android Developer Pleno"),
        ("j3", "Gerente de Tesouraria"),
    ]
    out = match_titles_in_message("rankeie candidatos da vaga Diretor Jurídico", jobs)
    assert out and out[0][0] == "j1"
    assert "j2" not in [i for i, _ in out]  # nao casa Android
    assert "j3" not in [i for i, _ in out]


def test_nao_casa_quando_nenhum_token_bate():
    jobs = [("j1", "Diretor(a) Jurídico(a)"), ("j2", "Android Developer")]
    out = match_titles_in_message("qual o clima hoje", jobs)
    assert out == []


def test_ordena_por_tokens_casados():
    jobs = [
        ("j1", "Engenheiro de Dados"),
        ("j2", "Engenheiro de Dados Sênior Pleno"),
    ]
    out = match_titles_in_message("vaga engenheiro de dados senior pleno", jobs)
    # j2 (mais tokens casados) deve vir antes
    assert out[0][0] == "j2"


def test_tokens_ignora_stopwords_e_acento():
    assert _tokens("Diretor(a) Jurídico(a)") == {"diretor", "juridico"}
    assert "vaga" not in _tokens("vaga de Diretor")


def test_titulo_de_1_token_casa_exato():
    jobs = [("j1", "Recrutador")]
    assert match_titles_in_message("perfil da vaga Recrutador", jobs)[0][0] == "j1"
    assert match_titles_in_message("vaga de Designer", jobs) == []
