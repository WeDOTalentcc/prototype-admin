import io, json, sys
EDITS = [
    ("messages/pt-BR.json",
     '      "createWithAI": "Criar com IA",\n      "refresh": "Atualizar",\n',
     '      "createWithAI": "Criar com IA",\n      "refresh": "Atualizar",\n      "statusCards": {\n        "managerNamePlaceholder": "Nome do gestor",\n        "newOffer": "Nova oferta"\n      },\n'),
    ("messages/en.json",
     '      "createWithAI": "Create with AI",\n      "refresh": "Refresh",\n',
     '      "createWithAI": "Create with AI",\n      "refresh": "Refresh",\n      "statusCards": {\n        "managerNamePlaceholder": "Manager name",\n        "newOffer": "New offer"\n      },\n'),
]
for path, needle, repl in EDITS:
    s = io.open(path, encoding="utf-8").read()
    if '"statusCards"' in s:
        print(f"{path}: already present"); continue
    if s.count(needle) != 1:
        print(f"{path}: ERROR count {s.count(needle)}"); sys.exit(1)
    io.open(path, "w", encoding="utf-8").write(s.replace(needle, repl))
    json.load(io.open(path, encoding="utf-8"))
    print(f"{path}: inserted + valid")
