# Comandos prontos

> Parte da skill `canonical-fix`. Carregue quando precisar deste topico especifico.

### Detectar duplicatas — frontend

```bash
# Hooks duplicados (mesmo nome em .ts e .tsx)
find plataforma-lia/src -type f \( -name "use-*.ts" -o -name "use-*.tsx" \) \
  | grep -v node_modules | grep -v ".next" \
  | xargs -n1 basename | sed 's/\.tsx\?$//' | sort | uniq -d

# Componentes com nome similar
find plataforma-lia/src -type f -name "*.tsx" | grep -v node_modules \
  | xargs -n1 basename | sort | uniq -d

# Mesmo export em multiplos arquivos
grep -rn "^export function useFoo\|^export const useFoo" plataforma-lia/src \
  --include="*.ts" --include="*.tsx" | grep -v node_modules

# Rotas Next.js duplicadas (mesmo path-segment final)
find plataforma-lia/src/app/api -name "route.ts" | sed 's|.*/api/||;s|/route.ts||' | sort | uniq -d
```

### Detectar duplicatas — backend

```bash
# Services com nome similar
find lia-agent-system/app -name "*service*.py" | grep -v __pycache__ \
  | xargs -n1 basename | sort | uniq -d

# Mesmo handler de rota
grep -rn "@router\.\(get\|post\|put\|delete\|patch\)" lia-agent-system/app \
  --include="*.py" | awk -F'"' '{print $2}' | sort | uniq -d

# Funcoes com mesmo nome em modulos diferentes
grep -rn "^def [a-z_]*\|^async def [a-z_]*" lia-agent-system/app --include="*.py" \
  | awk -F: '{print $3}' | sed 's/.*def \([a-z_][a-z_0-9]*\).*/\1/' | sort | uniq -c | sort -rn | head -20
```

### Mapear consumidores

```bash
# Quem importa o hook canonico
grep -rn "import.*useCandidatesExecuteSearch\|from.*useCandidatesExecuteSearch" \
  plataforma-lia/src --include="*.ts" --include="*.tsx" | grep -v node_modules

# Quem importa o service backend
grep -rn "from app\.services\.foo_service import\|FooService(" \
  lia-agent-system/app --include="*.py" | grep -v __pycache__

# Quem chama o endpoint
grep -rn "/api/backend-proxy/candidates\b\|/api/v1/candidates\b" \
  plataforma-lia/src lia-agent-system --include="*.ts" --include="*.tsx" --include="*.py"
```

### Detectar anti-padroes

```bash
# try/except engolindo erro
grep -rn -A1 "except.*:" lia-agent-system/app --include="*.py" \
  | grep -B1 "pass\|return \[\]\|return {}\|return None" | head -40

# Fallback silencioso no frontend
grep -rn "?? \[\]\|?? {}\||| \[\]\|catch.*=>.*\[\]" plataforma-lia/src \
  --include="*.ts" --include="*.tsx" | grep -v node_modules | head -40

# print() em codigo de producao
grep -rn "print(" lia-agent-system/app --include="*.py" | grep -v "test_\|^#"

# console.log de debug
grep -rn "console\.log" plataforma-lia/src --include="*.ts" --include="*.tsx" \
  | grep -v node_modules | grep -v ".next"

# Feature flags sem prazo de remocao
grep -rn "os\.getenv\|process\.env\." lia-agent-system/app plataforma-lia/src \
  --include="*.py" --include="*.ts" --include="*.tsx" | grep -i "use_new\|enable_new\|feature_"
```

---
