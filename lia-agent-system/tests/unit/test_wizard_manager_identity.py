"""Sensor canonical da captura deterministica do nome do gestor (audit 2026-06-05).

Pina o root-cause do bug do nome alucinado: no caminho ativo (orchestrator) o
inbound e mascarado (Presidio PERSON), o LLM fica cego ao nome e inventa
(Carlos Mendes -> Ricardo Almeida -> Rodrigo Silveira). A captura tem que ser
deterministica no servidor. Estes testes reproduzem a transcricao real.
"""
import pytest

from app.domains.job_creation.helpers.manager_identity import (
    derive_name_from_email,
    extract_manager_name_from_text,
)


class TestDeriveNameFromEmail:
    def test_paulo_moraes_email_do_caso_real(self):
        # Transcricao: "clt e o gestor e paulo.moraes@democompany.com.br"
        assert derive_name_from_email("paulo.moraes@democompany.com.br") == "Paulo Moraes"

    def test_underscore_e_hifen(self):
        assert derive_name_from_email("maria_clara@x.com") == "Maria Clara"
        assert derive_name_from_email("joao-silva@x.com") == "Joao Silva"

    def test_mailbox_generica_retorna_none(self):
        assert derive_name_from_email("rh@empresa.com") is None
        assert derive_name_from_email("vagas@empresa.com") is None
        assert derive_name_from_email("contato@empresa.com") is None

    def test_descarta_token_numerico(self):
        # Token puramente numerico e descartado (paulo.moraes.2 -> Paulo Moraes).
        assert derive_name_from_email("paulo.moraes.2@x.com") == "Paulo Moraes"

    def test_none_e_invalido(self):
        assert derive_name_from_email(None) is None
        assert derive_name_from_email("") is None
        assert derive_name_from_email("semarroba") is None


class TestExtractManagerNameFromText:
    def test_gestor_e_nome_direto(self):
        assert extract_manager_name_from_text("o gestor e Paulo Moraes") == "Paulo Moraes"

    def test_correcao_pega_o_ultimo_caso_real(self):
        # Transcricao: "eu nao falei o nome do gestor. nao e carlos mendes e paulo moraes"
        out = extract_manager_name_from_text(
            "eu nao falei o nome do gestor. nao e carlos mendes e paulo moraes"
        )
        assert out == "Paulo Moraes"

    def test_email_no_texto_nao_vira_nome(self):
        # "o gestor e paulo.moraes@x" -> NAO captura prefixo do email como nome;
        # a derivacao do email cuida disso separadamente.
        assert extract_manager_name_from_text("clt e o gestor e paulo.moraes@x.com") is None

    def test_sem_contexto_de_gestor_retorna_none(self):
        # "a vaga e senior" nao deve capturar "senior" como nome.
        assert extract_manager_name_from_text("a vaga e senior, departamento e tecnologia") is None

    def test_senioridade_nao_e_nome_mesmo_com_hint(self):
        assert extract_manager_name_from_text("e senior", manager_context_hint=True) is None

    def test_resposta_crua_com_hint(self):
        # LIA perguntou "qual o nome do gestor?" -> usuario responde so o nome.
        assert extract_manager_name_from_text("Paulo Moraes", manager_context_hint=True) == "Paulo Moraes"

    def test_resposta_crua_sem_hint_retorna_none(self):
        # Sem hint e sem contexto de gestor, "Paulo Moraes" solto nao e capturado
        # (evita capturar nome em contexto errado).
        assert extract_manager_name_from_text("Paulo Moraes") is None

    def test_reporta_a(self):
        assert extract_manager_name_from_text("ele reporta ao Carlos Andrade") == "Carlos Andrade"

    def test_nome_composto_com_conectivo(self):
        assert extract_manager_name_from_text("o gestor e Maria da Silva") == "Maria da Silva"

    def test_vazio(self):
        assert extract_manager_name_from_text(None) is None
        assert extract_manager_name_from_text("") is None


class TestSetJobFieldsIgnoraManagerName:
    """Boundary do orquestrador: o LLM NUNCA seta o nome do gestor (capturado
    server-side). Pina o root-cause da alucinacao (LLM passava 'Carlos Mendes').
    """

    def _ctx(self):
        from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
        return ToolContext(company_id="c1", user_id="u1", workspace_id=None)

    def test_manager_name_fora_do_settable(self):
        from app.domains.job_creation.orchestrator.wizard_tools import (
            _SETTABLE_JOB_FIELDS,
        )
        assert "manager_name" not in _SETTABLE_JOB_FIELDS

    def test_manager_name_no_schema_da_tool_removido(self):
        from app.domains.job_creation.orchestrator.wizard_tools import SET_JOB_FIELDS
        props = SET_JOB_FIELDS.input_schema["properties"]
        assert "manager_name" not in props

    def test_handler_ignora_manager_name_alucinado(self):
        from app.domains.job_creation.orchestrator.wizard_tools import (
            _handle_set_job_fields,
        )
        res = _handle_set_job_fields({}, {"manager_name": "Carlos Mendes"}, self._ctx())
        assert not res.error
        assert not (res.state_updates or {}).get("parsed_manager_name")
        assert "automaticamente" in res.llm_message.lower()

    def test_handler_aceita_outros_ignora_manager_name(self):
        from app.domains.job_creation.orchestrator.wizard_tools import (
            _handle_set_job_fields,
        )
        res = _handle_set_job_fields(
            {}, {"title": "Diretor", "manager_name": "Carlos Mendes"}, self._ctx()
        )
        assert not res.error
        assert res.state_updates.get("parsed_title") == "Diretor"
        assert "parsed_manager_name" not in (res.state_updates or {})
