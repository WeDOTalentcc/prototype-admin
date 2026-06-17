# Domain Template

Copy this directory to create a new domain.

## Agentic Domain (routable by CascadedRouter)

```bash
cp -r app/domains/_template/agentic app/domains/my_new_domain
# Then: rename all {domain_name} placeholders
```

## Service Domain (data/logic only, not routable)

```bash
cp -r app/domains/_template/service app/domains/my_new_domain
# Then: rename all {domain_name} placeholders
```

## Post-creation checklist

- [ ] Replace all `{domain_name}` placeholders with actual domain name
- [ ] Replace all `{DomainName}` placeholders with PascalCase name
- [ ] Update `config/capabilities.yaml` with real intent keywords
- [ ] Register in `agents_registry.yaml` (agentic only)
- [ ] Add mapping in `workflow.py` `_DOMAIN_TO_AGENT` (agentic only)
- [ ] Add entry in `app/domains/DOMAIN_CATALOG.md`
- [ ] Run: `python -m pytest tests/contract/test_domain_structure_conformance.py -v`
