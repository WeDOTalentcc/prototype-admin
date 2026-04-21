import importlib, sys, os, re
from pathlib import Path

BASE = Path("/home/runner/workspace/lia-agent-system")
sys.path.insert(0, str(BASE))
os.chdir(BASE)

def handler_exists(handler_path):
    parts = handler_path.rsplit(".", 1)
    if len(parts) != 2:
        return False
    module_path, attr = parts
    try:
        mod = importlib.import_module(module_path)
        return hasattr(mod, attr)
    except Exception:
        return False

domains_dir = BASE / "app" / "domains"
for tools_init in sorted(domains_dir.glob("*/tools/__init__.py")):
    source = tools_init.read_text()
    handlers = re.findall(r'"handler":\s*"([^"]+)"', source)
    broken = [h for h in handlers if not handler_exists(h)]
    if broken:
        print(f"\n{tools_init.relative_to(BASE)}: {len(broken)} broken")
        for h in broken:
            print(f"  - {h.rsplit('.', 1)[-1]}")
