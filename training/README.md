# ARLAW AI training and distillation

Fine-tuning is optional. Retrieval of current official law should remain the primary way to keep legal content current.

## Supervised LoRA / QLoRA

Install `training/requirements.txt`, prepare train and validation JSONL files matching `data_schema.json`, and mark each row `review_status: approved` only after qualified review. Every example must include jurisdiction, language, source IDs and an as-of date. Then run:

```bash
python training/train_lora.py --train data/train.jsonl --validation data/validation.jsonl --output artifacts/arlaw-adapter --model Qwen/Qwen3-1.7B
```

A compatible CUDA GPU is required. GPU availability and model compatibility vary; the script is not guaranteed to run on every free notebook runtime.

## Teacher/student distillation data preparation

Create a JSONL file containing `instruction`, `output`, `jurisdiction`, `language`, `source_ids`, `as_of`, `review_status`, and `teacher_model`. Teacher outputs must be checked by a qualified reviewer against the cited source material. Prepare accepted rows:

```bash
python training/build_distillation.py --input data/teacher_outputs.jsonl --output data/distillation_approved.jsonl
```

The script rejects unapproved or untraceable examples and writes a `.report.json` file. The resulting approved rows can be used as SFT training examples. This repository does not automatically generate trustworthy legal labels or replace expert review.

## Evaluation

Run the app and use `python evaluation/run_eval.py --base-url http://127.0.0.1:8000`. This is an API smoke test, not a legal accuracy benchmark. Build human-reviewed test sets covering jurisdiction, effective date, authority hierarchy, citation entailment, uncertainty and language quality.
