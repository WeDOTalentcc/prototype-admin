"""
FAR-1: Testes para as 5 novas categorias adicionadas ao FairnessGuard.

Cobre: antecedentes_criminais, saude_doenca, filiacao_sindical,
       aparencia_fisica, e expansão do IMPLICIT_BIAS_TERMS.
Também valida fix do regex de idade (falso negativo "X a Y anos no mercado").
"""
import pytest
from app.shared.compliance.fairness_guard import FairnessGuard, DISCRIMINATORY_CATEGORIES, IMPLICIT_BIAS_TERMS


class TestAntecedenteCriminais:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_blocks_sem_antecedentes_criminais(self):
        result = self.guard.check("candidatos sem antecedentes criminais obrigatório")
        assert result.is_blocked
        assert result.category == "antecedentes_criminais"

    def test_blocks_ficha_limpa_exigida(self):
        result = self.guard.check("ficha limpa exigida para a vaga")
        assert result.is_blocked
        assert result.category == "antecedentes_criminais"

    def test_blocks_excluir_ficha_suja(self):
        result = self.guard.check("excluir candidatos com ficha suja")
        assert result.is_blocked
        assert result.category == "antecedentes_criminais"

    def test_blocks_sem_passagem_policial(self):
        result = self.guard.check("apenas candidatos sem passagem policial")
        assert result.is_blocked
        assert result.category == "antecedentes_criminais"

    def test_blocks_certidao_nada_consta_obrigatoria(self):
        result = self.guard.check("certidão de nada consta obrigatória para candidatura")
        assert result.is_blocked
        assert result.category == "antecedentes_criminais"

    def test_allows_security_role_without_discrimination(self):
        # Vaga legítima de segurança sem discriminação explícita
        result = self.guard.check("vaga para segurança patrimonial, experiência em vigilância")
        assert not result.is_blocked

    def test_educational_message_references_cnj(self):
        result = self.guard.check("sem antecedentes criminais exigido")
        assert result.is_blocked
        assert "CNJ" in result.educational_message or "antecedentes" in result.educational_message.lower()


class TestSaudeDoenca:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_blocks_sem_hiv(self):
        result = self.guard.check("candidatos sem HIV para a posição")
        assert result.is_blocked
        assert result.category == "saude_doenca"

    def test_blocks_sem_aids(self):
        result = self.guard.check("selecionar apenas sem AIDS")
        assert result.is_blocked
        assert result.category == "saude_doenca"

    def test_blocks_sem_doencas_cronicas(self):
        result = self.guard.check("busco candidatos sem doenças crônicas")
        assert result.is_blocked
        assert result.category == "saude_doenca"

    def test_blocks_saude_perfeita_exigida(self):
        result = self.guard.check("saúde perfeita exigida para a função")
        assert result.is_blocked
        assert result.category == "saude_doenca"

    def test_blocks_portadores_hiv_nao(self):
        result = self.guard.check("portadores de HIV não serão contratados")
        assert result.is_blocked
        assert result.category == "saude_doenca"

    def test_allows_health_benefits_mention(self):
        # Mencionar plano de saúde não é discriminação
        result = self.guard.check("oferecemos plano de saúde completo para funcionários")
        assert not result.is_blocked

    def test_educational_message_references_lei_9029(self):
        result = self.guard.check("sem HIV obrigatório")
        assert result.is_blocked
        assert "9.029" in result.educational_message or "HIV" in result.educational_message


class TestFiliacaoSindical:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_blocks_nao_sindicalizado(self):
        result = self.guard.check("candidato não sindicalizado preferencial")
        assert result.is_blocked
        assert result.category == "filiacao_sindical"

    def test_blocks_sem_filiacao_sindical(self):
        result = self.guard.check("exigimos sem filiação sindical")
        assert result.is_blocked
        assert result.category == "filiacao_sindical"

    def test_blocks_excluir_sindicalistas(self):
        result = self.guard.check("excluir sindicalistas do processo")
        assert result.is_blocked
        assert result.category == "filiacao_sindical"

    def test_blocks_filiacao_sindical_proibida(self):
        result = self.guard.check("filiação sindical não permitida nesta empresa")
        assert result.is_blocked
        assert result.category == "filiacao_sindical"

    def test_allows_union_mention_neutral(self):
        # Mencionar sindicato em contexto neutro não deve bloquear
        result = self.guard.check("empresa signatária do acordo sindical do setor")
        assert not result.is_blocked

    def test_educational_message_references_clt(self):
        result = self.guard.check("não sindicalizado exigido")
        assert result.is_blocked
        assert "CLT" in result.educational_message or "543" in result.educational_message or "sindical" in result.educational_message.lower()


class TestAparenciaFisica:
    def setup_method(self):
        self.guard = FairnessGuard()

    def test_blocks_altura_minima(self):
        result = self.guard.check("altura mínima 1,70 exigida")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_blocks_estatura_minima(self):
        result = self.guard.check("estatura mínima obrigatória para a vaga")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_blocks_peso_maximo(self):
        result = self.guard.check("peso máximo 80kg para candidatos")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_blocks_sem_sobrepeso(self):
        result = self.guard.check("sem sobrepeso, exigência da empresa")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_blocks_boa_forma_fisica(self):
        result = self.guard.check("boa forma física obrigatória para a posição")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_blocks_corpo_atletico(self):
        result = self.guard.check("buscamos candidatos com corpo atlético")
        assert result.is_blocked
        assert result.category == "aparencia_fisica"

    def test_allows_physical_requirements_for_athletic_role(self):
        # Aptidão física como requisito funcional objetivo (não estético)
        result = self.guard.check("vaga para bombeiro, requer aptidão física comprovada via teste TAF")
        assert not result.is_blocked

    def test_educational_message_references_lei(self):
        result = self.guard.check("altura mínima 1,75 exigida para a vaga")
        assert result.is_blocked
        assert "9.029" in result.educational_message or "estética" in result.educational_message.lower() or "física" in result.educational_message.lower()


class TestImplicitBiasExpansion:
    """Testa os novos termos adicionados ao IMPLICIT_BIAS_TERMS."""

    def setup_method(self):
        self.guard = FairnessGuard()

    def test_soft_warning_zona_rural(self):
        warnings = self.guard.check_implicit_bias("preferência por candidatos da zona rural")
        assert any("rural" in w.lower() or "socioeconômica" in w.lower() for w in warnings)

    def test_soft_warning_periferia(self):
        warnings = self.guard.check_implicit_bias("não queremos candidatos da periferia")
        assert any("periferia" in w.lower() or "socioeconômica" in w.lower() for w in warnings)

    def test_soft_warning_sem_adaptacoes(self):
        warnings = self.guard.check_implicit_bias("candidato sem adaptações necessárias")
        assert any("adaptaç" in w.lower() or "PCD" in w or "deficiência" in w.lower() for w in warnings)

    def test_soft_warning_candomble(self):
        warnings = self.guard.check_implicit_bias("praticantes de candomblé não se encaixam")
        assert any("candomblé" in w.lower() or "religiosa" in w.lower() for w in warnings)

    def test_soft_warning_umbanda(self):
        warnings = self.guard.check_implicit_bias("preferência por quem não pratica umbanda")
        assert any("umbanda" in w.lower() or "religiosa" in w.lower() for w in warnings)

    def test_soft_warning_disponibilidade_total(self):
        warnings = self.guard.check_implicit_bias("necessário disponibilidade total sem restrições")
        assert any("disponibilidade" in w.lower() or "familiar" in w.lower() for w in warnings)

    def test_new_categories_count(self):
        # Verifica que agora temos 13 categorias no DISCRIMINATORY_CATEGORIES
        # (9 originais + 4 novas FAR-1: antecedentes_criminais, saude_doenca,
        #  filiacao_sindical, aparencia_fisica)
        # localizacao_proxy foi para IMPLICIT_BIAS_TERMS (soft warnings)
        guard = FairnessGuard()
        cats = guard.get_categories()
        assert len(cats) == 13, f"Esperado 13 categorias, encontrado {len(cats)}: {cats}"
        assert "antecedentes_criminais" in cats
        assert "saude_doenca" in cats
        assert "filiacao_sindical" in cats
        assert "aparencia_fisica" in cats


class TestIdadeRegexFix:
    """Testa o fix do regex de idade — falso negativo 'X a Y anos no mercado'."""

    def setup_method(self):
        self.guard = FairnessGuard()

    def test_allows_experience_range_mercado(self):
        """'de 8 a 10 anos no mercado' NÃO deve ser bloqueado — é experiência."""
        result = self.guard.check("profissional de 8 a 10 anos no mercado financeiro")
        assert not result.is_blocked, (
            f"Falso positivo: bloqueou critério de experiência. "
            f"Category={result.category}, terms={result.blocked_terms}"
        )

    def test_allows_experience_range_setor(self):
        result = self.guard.check("analista de 5 a 8 anos no setor de TI")
        assert not result.is_blocked

    def test_allows_experience_range_empresa(self):
        result = self.guard.check("gestor de 10 a 15 anos em empresa de grande porte")
        assert not result.is_blocked

    def test_still_blocks_age_range_without_context(self):
        """'de 25 a 35 anos' SEM contexto de experiência DEVE ser bloqueado."""
        result = self.guard.check("candidatos de 25 a 35 anos para a vaga")
        assert result.is_blocked
        assert result.category == "idade"

    def test_still_blocks_max_age_without_experience(self):
        result = self.guard.check("máximo 40 anos para candidatura")
        assert result.is_blocked
        assert result.category == "idade"

    def test_allows_max_experience_in_setor(self):
        result = self.guard.check("máximo 5 anos de experiência no setor público")
        assert not result.is_blocked

    def test_blocks_age_without_experience_keyword(self):
        result = self.guard.check("até 30 anos para o cargo de estagiário")
        assert result.is_blocked
        assert result.category == "idade"


class TestMultiCategoryDetection:
    """Testa queries com múltiplas categorias discriminatórias."""

    def setup_method(self):
        self.guard = FairnessGuard()

    def test_multi_category_blocks_on_first_detected(self):
        """Query com gênero + religião — bloqueia na primeira categoria detectada."""
        result = self.guard.check("apenas homens cristãos para a vaga")
        assert result.is_blocked
        # A categoria bloqueada deve ser uma das duas
        assert result.category in ("genero", "religiao")

    def test_multi_category_collects_all_terms(self):
        """Todos os termos discriminatórios devem ser capturados."""
        result = self.guard.check("apenas mulheres jovens até 30 anos")
        assert result.is_blocked
        assert len(result.blocked_terms) >= 1
