# RAG System

Multi-model RAG chatbot (Streamlit + GROQ) with PDF upload and benchmark analysis.

---

## View your project and benchmark (Streamlit Cloud)

Your app is already on Streamlit Cloud. After you push the new code:

- **Chatbot:** Open your app URL (e.g. `https://your-app-name.streamlit.app`) — this is the main **Multi Model RAG** chat.
- **Benchmark report:** In the **same app**, use the sidebar: click **Benchmark Report** to see the benchmark analysis. If you see "No benchmark results yet", run the benchmark locally once, then commit and push `benchmark/final_benchmark_results.json` (see below).

---

## Push the new benchmark to GitHub

In a terminal, from your project folder:

```bash
cd "c:\Users\sachi\Desktop\RAG System"
git add .
git status
git commit -m "Add benchmark analysis and Benchmark Report page"
git push origin main
```

After the push, Streamlit Cloud will redeploy. You will then have:

- **Multi Model RAG** (home) — chat and document Q&A
- **Benchmark Report** (sidebar) — benchmark results

To have real data on the Benchmark Report page: run the benchmark once on your PC (see "Run the benchmark" below), then add and push the generated JSON:

```bash
git add benchmark/final_benchmark_results.json
git commit -m "Add benchmark results"
git push origin main
```

---

## 1. Run the chatbot locally

From the project folder in a terminal:

```bash
cd "c:\Users\sachi\Desktop\RAG System"
pip install -r requirements.txt
streamlit run app.py
```

- Put your `GROQ_API_KEY` in a `.env` file in the project root.
- Browser will open at `http://localhost:8501`.
- Upload PDFs in the sidebar, click **Process Documents**, then ask questions in the chat.

---

## 2. Run the benchmark (local)

**Step A – Run the benchmark** (uses your PDF and GROQ):

```bash
cd "c:\Users\sachi\Desktop\RAG System"
python benchmark/run_benchmark.py "path\to\your\report.pdf"
```

Example if the PDF is on your Desktop:

```bash
python benchmark/run_benchmark.py "c:\Users\sachi\Desktop\AKSHITHA_YC_Major_Project_report.pdf"
```

This creates:

- `benchmark/final_benchmark_results.json`
- `benchmark/benchmark_report_standalone.html`

**Step B – View the benchmark**

- **In the same Streamlit app (after push):** Sidebar → **Benchmark Report** (if you committed `final_benchmark_results.json`).
- **Locally (standalone HTML):** Open `benchmark/benchmark_report_standalone.html` in your browser.

---

## 3. Push to GitHub (first time or new repo)

If the repo is already created on GitHub:

```bash
cd "c:\Users\sachi\Desktop\RAG System"
git add .
git status
git commit -m "Add RAG app, benchmark, and report"
git push origin main
```

If you have not created the repo yet:

1. On GitHub: **New repository** (e.g. `RAG-System`), do **not** add a README.
2. Locally, in the project folder:

```bash
cd "c:\Users\sachi\Desktop\RAG System"
git init
git add .
git commit -m "Initial commit: RAG chatbot and benchmark"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub username and repo name.

**Note:** `.env` is in `.gitignore`, so your API key is not pushed. Keep it secret.

---

## 4. Host the chatbot on Streamlit Cloud

You already mentioned hosting on Streamlit Cloud:

1. Push this project to GitHub (step 3).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in, **New app**.
3. Select the repo and set **Main file path** to `app.py`.
4. In **Secrets**, add: `GROQ_API_KEY = your_key`.
5. Deploy. Your chatbot will be at `https://your-app-name.streamlit.app`.

---

## Quick reference

| Goal                       | What to do |
|----------------------------|------------|
| View project (chatbot)      | Open your Streamlit Cloud URL (e.g. `https://your-app.streamlit.app`) |
| View benchmark in app      | Same URL → sidebar → **Benchmark Report** |
| Push new code to GitHub    | `git add .` → `git commit -m "Add benchmark"` → `git push origin main` |
| Run benchmark locally      | `python benchmark/run_benchmark.py "path\to\report.pdf"` |
| See benchmark on Cloud     | After running benchmark: commit `benchmark/final_benchmark_results.json` and push |
