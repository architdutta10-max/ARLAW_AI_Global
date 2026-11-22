import argparse,json
from pathlib import Path
import torch
from datasets import load_dataset
from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
from peft import LoraConfig,prepare_model_for_kbit_training
from trl import SFTTrainer,SFTConfig

SYSTEM=("You are ARLAW AI, a legal and economic research assistant. Never invent legal authorities "
        "or claim professional credentials. Identify jurisdiction and date, state uncertainty, "
        "and recommend verification against official primary sources.")

def validate(path):
    required={"instruction","output","jurisdiction","language","source_ids","as_of","review_status"}
    for n,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        row=json.loads(line); missing=required-set(row)
        if missing: raise ValueError(f"{path}:{n} missing {sorted(missing)}")
        if row["review_status"]!="approved" or not row["source_ids"]:
            raise ValueError(f"{path}:{n} requires expert approval and source_ids")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",required=True);p.add_argument("--validation",required=True)
    p.add_argument("--output",required=True);p.add_argument("--model",default="Qwen/Qwen3-1.7B")
    p.add_argument("--epochs",type=float,default=1);p.add_argument("--max-length",type=int,default=1024)
    a=p.parse_args()
    if not torch.cuda.is_available(): raise RuntimeError("CUDA GPU required; use a compatible local or cloud GPU.")
    validate(a.train);validate(a.validation)
    tok=AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token is None:tok.pad_token=tok.eos_token
    ds=load_dataset("json",data_files={"train":a.train,"validation":a.validation})
    def fmt(row):
        user=row["instruction"]+(("\n\nFacts/source excerpt:\n"+row.get("input","")) if row.get("input") else "")
        answer=f"Jurisdiction: {row['jurisdiction']}\nLanguage: {row['language']}\nAs of: {row['as_of']}\n{row['output']}"
        return {"text":tok.apply_chat_template([{"role":"system","content":SYSTEM},{"role":"user","content":user},{"role":"assistant","content":answer}],tokenize=False)}
    ds=ds.map(fmt)
    q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(a.model,quantization_config=q,device_map="auto")
    model=prepare_model_for_kbit_training(model)
    lora=LoraConfig(r=16,lora_alpha=32,lora_dropout=.05,bias="none",task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
    cfg=SFTConfig(output_dir=a.output,num_train_epochs=a.epochs,per_device_train_batch_size=1,
        per_device_eval_batch_size=1,gradient_accumulation_steps=8,learning_rate=2e-4,
        logging_steps=10,eval_strategy="steps",eval_steps=50,save_steps=50,save_total_limit=2,
        fp16=True,gradient_checkpointing=True,max_length=a.max_length,dataset_text_field="text",report_to="none")
    trainer=SFTTrainer(model=model,args=cfg,train_dataset=ds["train"],eval_dataset=ds["validation"],
                       processing_class=tok,peft_config=lora)
    trainer.train();trainer.save_model(a.output);tok.save_pretrained(a.output)
    print("Adapter saved:",a.output)
if __name__=="__main__":main()
