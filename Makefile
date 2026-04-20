.PHONY: glossary-sync glossary-check glossary-dry-run

glossary-sync:
	python3 scripts/glossary_sync.py

glossary-check:
	python3 scripts/glossary_sync.py --check

glossary-dry-run:
	python3 scripts/glossary_sync.py --dry-run
