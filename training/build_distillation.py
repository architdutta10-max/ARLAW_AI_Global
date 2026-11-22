"""Validate expert-reviewed teacher outputs and export student SFT/distillation JSONL."""
import argparse
import json
from pathlib import Path

REQUIRED = {"instruction", "output", "jurisdiction", "language", "source_ids", "as_of", "review_status", "teacher_model"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Teacher-generated JSONL with provenance")
    parser.add_argument("--output", required=True, help="Validated student-training JSONL")
    args = parser.parse_args()
    src, dst = Path(args.input), Path(args.output)
    accepted, rejected = [], []
    for line_no, raw in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
            missing = REQUIRED - set(row)
            if missing:
                raise ValueError(f"missing fields: {sorted(missing)}")
            if row["review_status"] != "approved":
                raise ValueError("teacher output is not expert-approved")
            if not row["source_ids"]:
                raise ValueError("source_ids must not be empty")
            if not row["output"].strip() or not row["instruction"].strip():
                raise ValueError("instruction/output must not be empty")
            accepted.append({k: row[k] for k in ("instruction", "output", "jurisdiction", "language", "source_ids", "as_of", "review_status")})
        except Exception as exc:
            rejected.append({"line": line_no, "reason": str(exc)})
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in accepted), encoding="utf-8")
    report = dst.with_suffix(dst.suffix + ".report.json")
    report.write_text(json.dumps({"accepted": len(accepted), "rejected": rejected}, indent=2), encoding="utf-8")
    print(f"Accepted {len(accepted)} approved examples; rejected {len(rejected)}. Report: {report}")
    if not accepted:
        raise SystemExit("No approved examples to train on.")

if __name__ == "__main__":
    main()
