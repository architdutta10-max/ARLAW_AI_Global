
from app.knowledge import search
from app.config import TOP_K
from app.llm import generate

question = "Compare Ohio civil rights law with federal anti-discrimination law."

hits = search(question, TOP_K, "GLOBAL")

context_parts = []
for i, hit in enumerate(hits, 1):
    context_parts.append(
        f"[S{i}] {hit['title']} | "
        f"Jurisdiction: {hit['jurisdiction']} | "
        f"Authority: {hit['authority']} | "
        f"Language: {hit['language']}\n"
        f"{hit['content']}"
    )

context = "\n\n".join(context_parts)

print("TOP_K:", TOP_K)
print("HITS:", len(hits))
print("CONTEXT CHARACTERS:", len(context))
print("SOURCE TITLES:", [h["title"] for h in hits])

answer, error, model = generate(
    [{"role": "user", "content": question}],
    context,
    [f"S{i}" for i in range(1, len(hits) + 1)]
)

print("ERROR:", error)
print("ANSWER LENGTH:", len(answer or ""))
print("MODEL:", model)
