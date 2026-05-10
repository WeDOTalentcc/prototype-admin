"""Coverage tests for intent_yaml_validator.py — pure validation functions."""
import os
import tempfile

import pytest
import yaml

from app.shared.services.intent_yaml_validator import validate_domain_yaml_sync


class TestValidateDomainYamlSync:
    def _write_yaml(self, tmpdir, data):
        config_dir = os.path.join(tmpdir, "config")
        os.makedirs(config_dir, exist_ok=True)
        yaml_path = os.path.join(config_dir, "capabilities.yaml")
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
        return tmpdir

    def test_missing_yaml_returns_no_yaml_status(self, tmp_path):
        result = validate_domain_yaml_sync(str(tmp_path), {})
        assert result["status"] == "no_yaml"

    def test_valid_yaml_returns_ok(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["busca", "search"]}]
        }
        self._write_yaml(str(tmp_path), data)
        keyword_map = {"busca": "search_action", "search": "search_action"}
        result = validate_domain_yaml_sync(str(tmp_path), keyword_map)
        assert result["status"] == "ok"

    def test_missing_in_yaml_reported(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["busca"]}]
        }
        self._write_yaml(str(tmp_path), data)
        keyword_map = {"busca": "act1", "extra_key": "act2"}
        result = validate_domain_yaml_sync(str(tmp_path), keyword_map)
        assert result["status"] == "ok"
        assert "extra_key" in result["missing_in_yaml"]

    def test_missing_in_dict_reported(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["busca", "yaml_only_key"]}]
        }
        self._write_yaml(str(tmp_path), data)
        keyword_map = {"busca": "act1"}
        result = validate_domain_yaml_sync(str(tmp_path), keyword_map)
        assert "yaml_only_key" in result["missing_in_dict"]

    def test_perfect_sync_no_drift(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["busca", "search"]}]
        }
        self._write_yaml(str(tmp_path), data)
        keyword_map = {"busca": "act1", "search": "act2"}
        result = validate_domain_yaml_sync(str(tmp_path), keyword_map)
        assert result["missing_in_yaml"] == []
        assert result["missing_in_dict"] == []

    def test_empty_keyword_map(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["busca"]}]
        }
        self._write_yaml(str(tmp_path), data)
        result = validate_domain_yaml_sync(str(tmp_path), {})
        assert result["status"] == "ok"
        assert "busca" in result["missing_in_dict"]

    def test_returns_domain_id(self, tmp_path):
        data = {
            "domain_id": "my_domain",
            "intents": []
        }
        self._write_yaml(str(tmp_path), data)
        result = validate_domain_yaml_sync(str(tmp_path), {})
        assert result["domain_id"] == "my_domain"

    def test_keyword_counts_returned(self, tmp_path):
        data = {
            "domain_id": "test",
            "intents": [{"name": "search", "keywords": ["k1", "k2"]}]
        }
        self._write_yaml(str(tmp_path), data)
        result = validate_domain_yaml_sync(str(tmp_path), {"k1": "a", "k2": "b"})
        assert result["yaml_keywords_count"] == 2
        assert result["dict_keywords_count"] == 2

    def test_corrupted_yaml_returns_error(self, tmp_path):
        config_dir = os.path.join(str(tmp_path), "config")
        os.makedirs(config_dir)
        with open(os.path.join(config_dir, "capabilities.yaml"), "w") as f:
            f.write("{ invalid yaml :: [")
        result = validate_domain_yaml_sync(str(tmp_path), {})
        assert result["status"] == "error"
