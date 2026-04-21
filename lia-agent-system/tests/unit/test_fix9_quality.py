"""
FIX 9 — Examples quality gate.

After regenerating weak examples, fewer than 10% of all examples should be
'isso'-fallback heuristic (down from 18% baseline).
"""


class TestFix9ExampleQuality:
    def test_weak_example_ratio_below_ten_percent(self):
        from app.domains.registry import DomainRegistry

        # Try all registered domains
        registry = DomainRegistry()
        total = 0
        weak = 0
        weak_list = []
        for domain_id in registry.list_domains():
            domain = registry.get_instance(domain_id)
            if not domain:
                continue
            for a in domain.get_allowed_actions():
                for ex in getattr(a, "examples", ()) or ():
                    total += 1
                    low = ex.lower().strip()
                    if "isso" in low:
                        weak += 1
                        weak_list.append(f"{domain_id}.{a.action_id}: {ex}")

        assert total > 0, "No examples found — registry empty?"
        ratio = weak / total
        assert ratio < 0.10, (
            f"Esperado <10% weak, got {100 * ratio:.1f}% ({weak}/{total}). "
            f"First 10 weak: {weak_list[:10]}"
        )

    def test_all_domains_still_have_examples(self):
        """Regression: no action lost its examples during FIX 9."""
        from app.domains.registry import DomainRegistry

        registry = DomainRegistry()
        for domain_id in registry.list_domains():
            domain = registry.get_instance(domain_id)
            if not domain:
                continue
            missing = [a.action_id for a in domain.get_allowed_actions() if not getattr(a, "examples", ())]
            assert not missing, f"{domain_id}: actions without examples after FIX 9: {missing[:5]}"
