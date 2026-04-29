# Replit Setup — Workflows e Logs

Este documento descreve a configuração canônica dos workflows do Replit
(o `.replit` está gitignored — esta doc é a fonte da verdade rastreável
para reconstruir a config do zero).

## Workflow `lia-backend` (FastAPI / uvicorn)

```toml
[[workflows.workflow]]
name = "lia-backend"
author = "agent"

[workflows.workflow.metadata]
outputType = "console"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "redis-server --daemonize yes 2>/dev/null; (fuser -k -KILL 8001/tcp 2>/dev/null || true); sleep 1; cd lia-agent-system && PYTHONUNBUFFERED=1 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 2>&1 | tee /tmp/lia-backend-stdout.log"
waitForPort = 8001
```

### Decisões de config (post-mortem 2026-04-29)

- **`PYTHONUNBUFFERED=1`** — força Python a fazer flush de stdout linha a
  linha em vez de bufferizar. Sem isso, o `tee` recebe blocos de logs
  só quando o buffer é cheio, mascarando latência real e dificultando
  debug em tempo real via `tail -F`.

- **`2>&1 | tee /tmp/lia-backend-stdout.log`** — duplica os logs para
  arquivo + console Replit. Sem o `tee`, todo restart de processo perde
  visibilidade dos logs via SSH (problema observado quando o uvicorn
  reiniciou às 18:36 do dia 2026-04-29 e logs viraram inacessíveis).
  O mesmo padrão é usado pelo workflow `eval-runner`.

- **Localização `/tmp/lia-backend-stdout.log`** — `/tmp` sobrevive a
  restart de processo, mas é limpado em cold-start do Repl. Se logs
  precisarem persistir entre cold-starts, mudar para
  `/home/runner/workspace/logs/lia-backend.log` (mas ocupa quota do Repl).

- **`fuser -k -KILL 8001/tcp`** — mata processo zumbi na porta 8001
  antes de subir o uvicorn. Necessário porque `uvicorn` falha silente se
  a porta já está ocupada.

### Verificação rápida

Após Restart do workflow no Replit, em terminal SSH:

```bash
tail -F /tmp/lia-backend-stdout.log | grep -E "ERROR|Traceback|rail_a"
```

Se logs não aparecem em ~10s após uma chamada de API, o `tee` não está
funcionando — checar se `PYTHONUNBUFFERED=1` está presente no `args`.

## Outros workflows críticos

### `eval-runner` (já com tee)

Padrão referência:

```bash
cd /home/runner/workspace/lia-agent-system && python3 -u eval/eval_runner.py 2>&1 | tee /tmp/eval20_full.log
```

Note `python3 -u` (unbuffered flag inline) em vez de `PYTHONUNBUFFERED=1` —
ambos funcionam, escolha um e mantenha consistência.

## Quando reconstruir o `.replit`

- Após cold-start de Repl que perdeu config local
- Após `git clean -dfx` ou `rm -rf .replit`
- Migrando para novo Repl

Aplicar a partir desta doc. NÃO improvisar — a falta de `tee` ou
`PYTHONUNBUFFERED` cria bugs silenciosos no debug que custam horas.

## Skill canônica

`harness-engineering [guide computacional]` — config persistente que
remove a categoria inteira de "logs sumiram após restart" do espaço de
problemas possíveis.
