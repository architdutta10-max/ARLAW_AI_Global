import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.knowledge import init_db,add_source

def read_file(p):
    if p.suffix.lower()==".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    return p.read_text(encoding="utf-8",errors="replace")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("folder",type=Path);ap.add_argument("--jurisdiction",default="Unspecified")
    ap.add_argument("--as-of",default="");ap.add_argument("--source-url",default="")
    a=ap.parse_args();init_db()
    for p in a.folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".txt",".md",".pdf"}:
            try:
                result=add_source(p.stem,read_file(p),a.jurisdiction,a.source_url,a.as_of,p.name)
                print("Indexed",p,result)
            except Exception as e: print("Skipped",p,e)
