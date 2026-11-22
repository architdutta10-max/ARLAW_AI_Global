"""Small API smoke/evaluation runner for a running ARLAW AI instance."""
import argparse, json, sys
import requests

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--questions", default="evaluation/sample_questions.jsonl")
    args = p.parse_args()
    base = args.base_url.rstrip("/")
    health = requests.get(base + "/api/health", timeout=15); health.raise_for_status()
    rows = [json.loads(x) for x in open(args.questions, encoding="utf-8") if x.strip()]
    failures = 0
    for i, row in enumerate(rows, 1):
        response = requests.post(base + "/api/chat", json={"messages": [{"role": "user", "content": row["question"]}], "jurisdiction": row.get("jurisdiction", "GLOBAL")}, timeout=300)
        response.raise_for_status(); data = response.json()
        ok = bool(data.get("answer")) and data.get("model_connected") is True
        failures += not ok
        print(json.dumps({"case": i, "ok": ok, "task": data.get("task"), "provider": data.get("model", {}).get("provider"), "citation_validation": data.get("citation_validation")}, ensure_ascii=False))
    print(f"Completed {len(rows)} cases; failures={failures}")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
