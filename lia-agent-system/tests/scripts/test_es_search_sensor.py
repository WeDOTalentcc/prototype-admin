"""Sentinel for scripts/check_es_search_has_tenant_filter.py (Task #1147)."""
from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_es_search_has_tenant_filter.py"


def _load_sensor():
    spec = importlib.util.spec_from_file_location(
        "es_search_sensor_under_test", SCRIPT_PATH
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_app(tmp_path: Path, body: str) -> Path:
    pkg = tmp_path / "app" / "domains" / "x" / "services"
    pkg.mkdir(parents=True)
    target = pkg / "svc.py"
    target.write_text(textwrap.dedent(body))
    return target


def test_sensor_flags_es_search_without_wrapper(tmp_path, monkeypatch, capsys):
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        async def bad(es, cid):
            return await es.search(index="candidates", body={"query": {"match_all": {}}})
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "not produced by with_tenant_filter" in err


def test_sensor_passes_when_wrapper_used(tmp_path, monkeypatch, capsys):
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def good(es, cid):
            body = with_tenant_filter({"query": {"match_all": {}}}, cid)
            return await es.search(index="candidates", body=body)
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    assert rc == 0


def test_sensor_passes_with_inline_wrapper(tmp_path, monkeypatch):
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def inline(es, cid):
            return await es.search(
                index="candidates",
                body=with_tenant_filter({"query": {"match_all": {}}}, cid),
            )
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    assert sensor.main(["--block"]) == 0


def test_sensor_ignores_re_search_and_self_search(tmp_path, monkeypatch):
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        import re

        class Repo:
            async def list(self):
                return await self.search("x")  # service-internal, not ES

        def parse(text):
            return re.search(r"foo", text)

        def count_names(names):
            return names.count("alice")
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    assert sensor.main(["--block"]) == 0


def test_sensor_respects_allowlist(tmp_path, monkeypatch):
    sensor = _load_sensor()
    target = _write_app(
        tmp_path,
        """
        async def health(es):
            return await es.count(index="candidates", body={"query": {"match_all": {}}})
        """,
    )
    rel = target.relative_to(tmp_path).as_posix()
    allow = tmp_path / "allow.txt"
    allow.write_text(f"{rel}\n")
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", allow)
    assert sensor.main(["--block"]) == 0


def test_sensor_flags_unrelated_wrapper_in_same_function(tmp_path, monkeypatch, capsys):
    """Bypass attempt: wrapper called on a DIFFERENT variable than the one
    passed to es.search. Must still flag the ES call."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def bypass_diff_var(es, cid):
            other = with_tenant_filter({"query": {"match_all": {}}}, cid)
            body = {"query": {"match_all": {}}}
            return await es.search(index="candidates", body=body)
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "body not produced by with_tenant_filter" in err


def test_sensor_flags_wrapper_after_es_call(tmp_path, monkeypatch, capsys):
    """Bypass attempt: wrapper called AFTER the ES call. Must flag."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def wrapper_too_late(es, cid):
            body = {"query": {"match_all": {}}}
            result = await es.search(index="candidates", body=body)
            body = with_tenant_filter(body, cid)
            return result
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "body not produced by with_tenant_filter" in err


def test_sensor_flags_reassignment_after_wrapper(tmp_path, monkeypatch, capsys):
    """Bypass attempt: wrapper result reassigned to plain dict before ES call."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def reassigned(es, cid):
            body = with_tenant_filter({"query": {"match_all": {}}}, cid)
            body = {"query": {"match_all": {}}}  # clobbers the wrapper
            return await es.search(index="candidates", body=body)
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "body not produced by with_tenant_filter" in err


def test_sensor_flags_dict_literal_body(tmp_path, monkeypatch, capsys):
    """Body passed as a dict literal (not a Name) must be flagged even if
    a wrapper call exists elsewhere in the function."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def literal_body(es, cid):
            _ = with_tenant_filter({}, cid)  # unrelated
            return await es.search(
                index="candidates",
                body={"query": {"match_all": {}}},
            )
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "body not produced by with_tenant_filter" in err


def test_sensor_flags_aug_assign_after_wrapper(tmp_path, monkeypatch, capsys):
    """AugAssign (body |= {...}) after wrapper must be treated as
    reassignment and the ES call flagged."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def aug_clobber(es, cid):
            body = with_tenant_filter({}, cid)
            body |= {"size": 10}
            return await es.search(index="candidates", body=body)
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1


def test_sensor_flags_body_kwarg_without_index_kwarg(tmp_path, monkeypatch, capsys):
    """Bypass attempt: ``es.search(body=...)`` without ``index=``. Sensor
    must still classify it as an ES call and flag the missing wrapper."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        async def bypass_no_index(es):
            return await es.search(body={"query": {"match_all": {}}})
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    rc = sensor.main(["--block"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "body not produced by with_tenant_filter" in err


def test_sensor_passes_with_safe_reassignment(tmp_path, monkeypatch):
    """Re-wrapping after a clobber should pass — the most-recent reaching
    assignment before the call is the wrapper."""
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        from app.shared.search import with_tenant_filter

        async def rewrapped(es, cid):
            body = {"query": {"match_all": {}}}
            body = with_tenant_filter(body, cid)
            return await es.search(index="candidates", body=body)
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    assert sensor.main(["--block"]) == 0


def test_sensor_warn_mode_returns_zero(tmp_path, monkeypatch):
    sensor = _load_sensor()
    _write_app(
        tmp_path,
        """
        async def bad(es):
            return await es.search(index="x", body={"query": {"match_all": {}}})
        """,
    )
    monkeypatch.setattr(sensor, "ROOT", tmp_path)
    monkeypatch.setattr(sensor, "APP_DIR", tmp_path / "app")
    monkeypatch.setattr(sensor, "ALLOWLIST_FILE", tmp_path / "missing.txt")
    assert sensor.main(["--warn"]) == 0


def test_sensor_scans_real_codebase_clean():
    """The real production tree must pass after the Task #1147 sweep."""
    sensor = _load_sensor()
    # No monkeypatch — exercise the actual paths.
    rc = sensor.main(["--block"])
    assert rc == 0, "production tree has an unwrapped es.search/es.count callsite"
