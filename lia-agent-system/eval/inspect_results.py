import json, ast
data = json.load(open("/home/runner/workspace/lia-agent-system/eval/eval_results_20260417_175913.json"))
critical = ["JM-001","JM-007","SC-001","CO-001","WZ-001","CX-002","SO-006","EX-004"]
for r in data:
    if r["id"] in critical:
        print("=== {} | score={} | {}ms ===".format(r["id"], r["score"], r["latency_ms"]))
        resp = r["response"]
        if isinstance(resp, str) and resp.startswith("{"):
            try:
                d = ast.literal_eval(resp)
                msg = d.get("data",{}).get("message",{})
                content = msg.get("content") or msg.get("text") or str(msg)
                print(repr(content[:400]))
            except Exception as e:
                print("parse_err:", e, repr(resp[:300]))
        elif resp:
            print(repr(resp[:400]))
        elif r.get("error"):
            print("ERROR:", r["error"])
        print()
