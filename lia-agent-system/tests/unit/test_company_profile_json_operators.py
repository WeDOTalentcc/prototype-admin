"""
TDD test — FIX 1: company_profile_repository.py JSON operators.

Verifica que os operadores JSON usados nas queries de workforce_plan
usam aspas simples em torno das chaves, conforme sintaxe PostgreSQL.

Bug: ->workforce_plan (sem aspas) => PostgreSQL trata como coluna inexistente.
Fix: ->'workforce_plan' (com aspas) => chave JSON string.
"""
import re
import inspect
import unittest


class TestCompanyProfileJsonOperators(unittest.TestCase):

    def _get_repo_source(self):
        import sys
        sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
        from app.domains.company_settings.repositories.company_profile_repository import (
            CompanyProfileRepository,
        )
        return inspect.getsource(CompanyProfileRepository)

    def test_get_workforce_plan_no_unquoted_json_arrow(self):
        """additional_data->workforce_plan sem aspas NAO deve aparecer."""
        source = self._get_repo_source()
        # Operador -> imediatamente seguido de workforce_plan sem aspas
        # Regex: -> depois de qualquer char, seguido de workforce_plan sem aspas antes/depois
        invalid = re.compile(r"->workforce_plan")
        self.assertIsNone(
            invalid.search(source),
            "Bug: 'additional_data->workforce_plan' sem aspas encontrado. "
            "PostgreSQL trata workforce_plan como coluna. "
            "Fix: ->'\''workforce_plan'\''"
        )

    def test_get_workforce_plan_has_quoted_json_arrow(self):
        """A query deve usar ->'workforce_plan' (com aspas simples)."""
        source = self._get_repo_source()
        # Aceitar: ->'workforce_plan' ou ->>'workforce_plan'
        valid = re.compile(r"->>'?workforce_plan'?")
        # Mais especifico: requer aspas
        valid_quoted = re.compile(r"->'workforce_plan'|->>'workforce_plan'")
        self.assertIsNotNone(
            valid_quoted.search(source),
            "Nao encontrado ->'workforce_plan' com aspas. Fix necessario."
        )

    def test_jsonb_set_path_is_array_literal(self):
        """jsonb_set path deve ser '{workforce_plan}' (com aspas simples ao redor)."""
        source = self._get_repo_source()
        # Padrao invalido: virgula, espaco, {workforce_plan} sem aspas
        invalid = re.compile(r",\s*\{workforce_plan\}\s*,")
        self.assertIsNone(
            invalid.search(source),
            "Bug: jsonb_set path '{workforce_plan}' sem aspas. "
            "PostgreSQL espera o path como string literal: '{workforce_plan}'"
        )

    def test_jsonb_build_object_key_is_string_literal(self):
        """jsonb_build_object('workforce_plan', ...) — chave deve ter aspas."""
        source = self._get_repo_source()
        # Padrao invalido: jsonb_build_object( workforce_plan sem aspas
        invalid = re.compile(r"jsonb_build_object\(\s*workforce_plan\s*,")
        self.assertIsNone(
            invalid.search(source),
            "Bug: jsonb_build_object(workforce_plan, sem aspas. "
            "Fix: jsonb_build_object('workforce_plan', ...)"
        )


if __name__ == "__main__":
    unittest.main()
