"""Tests TDD P0-2: _build_competencies_from_enriched_jd suporta múltiplos formatos."""
import sys
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

from app.domains.cv_screening.services.wsi_service.service import WSIService


def test_reads_new_format_flat_lists():
    blob = {
        "technical_skills": ["Python", "Docker", "React"],
        "behavioral_competencies": ["Liderança", "Comunicação"],
        "responsibilities": ["Gerenciar time"],
        "description": "Engenheiro sênior",
    }
    comps, ctx = WSIService._build_competencies_from_enriched_jd(blob, "senior")
    tech = [c for c in comps if c.type == "technical"]
    behav = [c for c in comps if c.type == "behavioral"]
    assert len(tech) == 3, f"Esperado 3 técnicas, got {len(tech)}"
    assert len(behav) == 2, f"Esperado 2 comportamentais, got {len(behav)}"
    assert any(c.name == "Python" for c in tech)
    assert "Engenheiro sênior" in ctx
    print("PASS: test_reads_new_format_flat_lists")

def test_reads_legacy_format():
    blob = {
        "skills_obrigatorias": ["Java", "PostgreSQL"],
        "competencias_comportamentais": ["Proatividade"],
        "responsabilidades": ["Desenvolver APIs"],
        "about_role": "Backend developer",
    }
    comps, ctx = WSIService._build_competencies_from_enriched_jd(blob)
    tech = [c for c in comps if c.type == "technical"]
    behav = [c for c in comps if c.type == "behavioral"]
    assert len(tech) == 2, f"Esperado 2, got {len(tech)}"
    assert len(behav) == 1, f"Esperado 1, got {len(behav)}"
    assert "Backend developer" in ctx
    print("PASS: test_reads_legacy_format")

def test_reads_section_suggestions_format():
    blob = {
        "technical_skills": {
            "detected_items": ["Python"],
            "suggestions": [{"id": "t1", "value": "Docker"}, {"id": "t2", "value": "K8s"}]
        },
        "behavioral_competencies": {
            "detected_items": ["Liderança"],
            "suggestions": [{"id": "b1", "value": "Comunicação", "big_five_mapping": "agreeableness"}]
        },
    }
    comps, ctx = WSIService._build_competencies_from_enriched_jd(blob)
    tech = [c for c in comps if c.type == "technical"]
    behav = [c for c in comps if c.type == "behavioral"]
    assert len(tech) == 3, f"Esperado 3 (1 detected + 2 sug), got {len(tech)}"
    assert len(behav) == 2, f"Esperado 2, got {len(behav)}"
    comm = next((c for c in behav if c.name == "Comunicação"), None)
    assert comm and comm.big_five_mapping == "agreeableness"
    print("PASS: test_reads_section_suggestions_format")

def test_new_format_wins_over_legacy():
    blob = {
        "technical_skills": ["Python", "Go"],
        "skills_obrigatorias": ["COBOL"],
        "behavioral_competencies": ["Foco"],
        "competencias_comportamentais": ["Lentidão"],
    }
    comps, _ = WSIService._build_competencies_from_enriched_jd(blob)
    names = [c.name for c in comps]
    assert "Python" in names and "Go" in names
    assert "COBOL" not in names, "Legado não deve aparecer quando novo existe"
    assert "Foco" in names
    assert "Lentidão" not in names
    print("PASS: test_new_format_wins_over_legacy")

def test_empty_blob():
    comps, ctx = WSIService._build_competencies_from_enriched_jd({})
    assert comps == [] and ctx == ""
    print("PASS: test_empty_blob")

if __name__ == "__main__":
    failed = 0
    for t in [test_reads_new_format_flat_lists, test_reads_legacy_format,
              test_reads_section_suggestions_format, test_new_format_wins_over_legacy,
              test_empty_blob]:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__} — {e}")
            failed += 1
    print(f"\n{'TODOS PASSARAM' if not failed else f'{failed} FALHARAM'} ({5-failed}/5)")
    sys.exit(failed)
