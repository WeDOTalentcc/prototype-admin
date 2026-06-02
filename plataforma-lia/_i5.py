#!/usr/bin/env python3
import io, json, sys
EDITS = [
    ("messages/pt-BR.json", '      "refresh": "Atualizar",\n',
     '      "refresh": "Atualizar",\n      "statusCards": {\n        "managerNamePlaceholder": "Nome do gestor",\n        "newOffer": "Nova oferta"\n      },\n'),
    ("messages/en.json", '      "refresh": "Refresh",\n',
     '      "refresh": "Refresh",\n      "statusCards": {\n        "managerNamePlaceholder": "Manager name",\n        "newOffer": "New offer"\n      },\n'),
]
for path, needle, repl in EDITS:
    s = io.open(path, encoding="utf-8").read()
    if '"statusCards"' in s:
        print(f"{path}: statusCards already present, skipping"); continue
    if s.count(needle) != 1:
        print(f"{path}: ERROR needle count {s.count(needle)}"); sys.exit(1)
    io.open(path, "w", encoding="utf-8").write(s.replace(needle, repl))
    json.load(io.open(path, encoding="utf-8"))
    print(f"{path}: inserted statusCards + valid")
