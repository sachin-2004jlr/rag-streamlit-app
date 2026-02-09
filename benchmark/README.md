# RAG Benchmark

Benchmark the RAG system using the Helmet and License Plate Detection Major Project report (or any PDF). The report page follows the structure of [RAG Performance Matrix | Executive Report](https://palanisuhas.github.io/vectordb-research/).

## Prerequisites

- Python environment with project dependencies installed (`requirements.txt`)
- `.env` in project root with `GROQ_API_KEY`
- A PDF to benchmark (e.g. the Major Project report)

## Run the benchmark

From the **project root** (RAG System):

```bash
python benchmark/run_benchmark.py path/to/AKSHITHA_YC_Major_Project_report.pdf
```

Optional:

- `--model llama-3.1-8b-instant` (default: `llama-3.3-70b-versatile`)
- `--output-dir benchmark` (default: `benchmark/`)

Outputs:

- `benchmark/final_benchmark_results.json` – raw results
- `benchmark/benchmark_report_standalone.html` – report with embedded data (open in browser as file or via server)

## View the report

- **With a local server** (recommended): from project root run  
  `python -m http.server 8000`  
  then open:  
  `http://localhost:8000/benchmark/benchmark_report.html`  
  The page loads `final_benchmark_results.json` from the same directory.

- **Standalone (no server)**: open `benchmark/benchmark_report_standalone.html` in your browser. All data is embedded, so it works from `file://`.

## Questions (8)

1. **Objective and problem statement** – Main goal and problem statement of the project.
2. **Algorithms and methodology** – Models used for helmet and license plate (e.g. YOLO, OCR) and why.
3. **Performance metrics** – Reported accuracy, precision, recall, mAP.
4. **Limitations** – Low-light, OCR, generalization, etc.
5. **Future enhancements** – Proposed improvements for helmet and license plate.
6. **Dataset and training** – Dataset sizes, epochs, batch size, image size for both tasks.
7. **System architecture** – High-level data flow from input to detection and OCR.
8. **Testing and validation** – Unit/integration/system testing and KPIs.

Edit `benchmark_questions.json` to change or add questions.

## Report metrics

Each run records **latency (ms)** and **similarity score** (top retrieval score). The report shows an **average similarity** in System Stats and **Sources** (top 3 chunks with scores) per question.
