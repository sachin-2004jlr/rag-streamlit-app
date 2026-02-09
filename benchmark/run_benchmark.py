"""
RAG Benchmark Runner
Processes the specified PDF with the RAG pipeline and runs five benchmark questions.
Outputs final_benchmark_results.json and optionally an HTML report with embedded data.
"""
import os
import sys
import json
import shutil
import time
import argparse
from pathlib import Path
from datetime import datetime

# Ensure project root is on path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

from src.backend import AdvancedRAG


def embed_benchmark_html(output_dir: Path, result: dict) -> None:
    """Write a copy of the report HTML with JSON embedded so it works when opened as file://."""
    report_path = SCRIPT_DIR / "benchmark_report.html"
    standalone_path = output_dir / "benchmark_report_standalone.html"
    if not report_path.exists():
        return
    html = report_path.read_text(encoding="utf-8")
    payload = json.dumps(result, ensure_ascii=False)
    # Avoid </script> in payload breaking the HTML parser
    payload = payload.replace("</", "\\u003c/")
    script_tag = '<script type="application/json" id="benchmark-data">' + payload + "</script>\n  "
    html = html.replace("</head>", script_tag + "</head>")
    standalone_path.write_text(html, encoding="utf-8")
    print(f"Standalone report written to {standalone_path}")


def _system_stats(runs: list) -> dict:
    scores = [r["similarity_score"] for r in runs if r.get("similarity_score") is not None]
    avg = round(sum(scores) / len(scores), 4) if scores else None
    return {
        "runs": len(runs),
        "docs": 1,
        "total_questions": len(runs),
        "total_latency_ms": round(sum(r["latency_ms"] for r in runs), 2),
        "avg_similarity_score": avg
    }


def _build_executive_summary(doc_name: str, model_name: str, runs: list, result: dict) -> str:
    total_ms = result["system_stats"]["total_latency_ms"]
    n = len(runs)
    scores = [r.get("similarity_score") for r in runs if r.get("similarity_score") is not None]
    avg_score = (sum(scores) / len(scores)) if scores else None
    parts = [
        f"Benchmark completed on {doc_name} with model {model_name}.",
        f"{n} questions executed successfully.",
        f"Total query latency: {total_ms:.2f} ms.",
    ]
    if avg_score is not None:
        parts.append(f"Average top retrieval similarity score: {avg_score:.4f}.")
    return " ".join(parts)


def load_questions(questions_path: Path) -> dict:
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(pdf_path: str, model_name: str = "llama-3.3-70b-versatile", output_dir: Path = None):
    if output_dir is None:
        output_dir = SCRIPT_DIR
    questions_path = SCRIPT_DIR / "benchmark_questions.json"
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    questions_data = load_questions(questions_path)
    rag = AdvancedRAG()

    # Isolate benchmark run: dedicated temp dir for files and DB
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_dir = SCRIPT_DIR / "temp_benchmark_files"
    db_dir = SCRIPT_DIR / "temp_benchmark_db"
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)

    try:
        # Copy PDF into benchmark files dir
        dest_pdf = files_dir / pdf_path.name
        shutil.copy2(pdf_path, dest_pdf)

        # Process documents
        status = rag.process_documents(str(files_dir), str(db_dir))
        if status != "Success":
            return {"error": status, "results": None}

        # Run each question and record response, latency, sources, similarity score
        runs = []
        for q in questions_data["questions"]:
            start = time.perf_counter()
            try:
                out = rag.query_with_sources(
                    query_text=q["question"],
                    db_path=str(db_dir),
                    model_name=model_name,
                    top_k_sources=3
                )
                answer = out["answer"]
                top_score = out.get("top_similarity_score")
                sources = out.get("sources") or []
            except Exception as e:
                answer = f"Error: {str(e)}"
                top_score = None
                sources = []
            elapsed_ms = (time.perf_counter() - start) * 1000
            runs.append({
                "id": q["id"],
                "category": q["category"],
                "question": q["question"],
                "answer": answer,
                "latency_ms": round(elapsed_ms, 2),
                "similarity_score": round(top_score, 4) if top_score is not None else None,
                "sources": sources
            })

        # Build output structure (aligned with reference: System Stats, Runs, Docs, Executive)
        doc_name = pdf_path.name
        result = {
            "meta": {
                "run_id": run_id,
                "run_date": datetime.now().isoformat(),
                "source_file": doc_name,
                "model": model_name,
                "description": questions_data.get("description", "")
            },
            "system_stats": _system_stats(runs),
            "benchmark_summary": {
                "source_document": doc_name,
                "model_used": model_name,
                "questions_evaluated": len(runs),
                "status": "Success"
            },
            "runs": runs,
            "executive_summary": _build_executive_summary(doc_name, model_name, runs, result)
        }

        # Write JSON
        out_json = output_dir / "final_benchmark_results.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results written to {out_json}")

        # Write standalone HTML with embedded JSON (for local file open)
        embed_benchmark_html(output_dir, result)
        return result
    finally:
        if os.path.exists(files_dir):
            shutil.rmtree(files_dir, ignore_errors=True)
        if os.path.exists(db_dir):
            shutil.rmtree(db_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Run RAG benchmark on a PDF.")
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF document (e.g. AKSHITHA_YC_Major_Project_report.pdf)"
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="GROQ model ID (default: llama-3.3-70b-versatile)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for final_benchmark_results.json (default: benchmark/)"
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else SCRIPT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    result = run_benchmark(args.pdf_path, model_name=args.model, output_dir=output_dir)
    if result.get("error"):
        print(result["error"])
        sys.exit(1)


if __name__ == "__main__":
    main()
