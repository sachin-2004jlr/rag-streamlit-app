import streamlit as st
import json
import os

st.set_page_config(page_title="Benchmark Report | RAG", layout="wide", initial_sidebar_state="expanded")

# Same dark theme as main app
st.markdown("""
<style>
.stApp { background-color: #0e1117; }
.bench-title { font-family: 'Inter', sans-serif; color: #f3f4f6; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
.bench-subtitle { color: #6b7280; font-size: 0.85rem; margin-bottom: 1.5rem; }
.bench-section { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: #6b7280; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #1f2937; padding-bottom: 0.5rem; }
.bench-stat { background: #161922; border: 1px solid #252836; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; }
.bench-stat-val { font-size: 1.5rem; color: #e8eaed; }
.bench-stat-lbl { font-size: 0.75rem; color: #9aa0a6; }
.bench-card { background: #161922; border: 1px solid #252836; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
.bench-q { font-weight: 600; color: #e8eaed; margin-bottom: 0.5rem; }
.bench-a { color: #9aa0a6; font-size: 0.9rem; line-height: 1.6; }
.bench-meta { font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem; }
.bench-exec { border-left: 4px solid #4a9eff; padding-left: 1rem; color: #9aa0a6; font-size: 0.95rem; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)

# Path resolution that works both locally and on Streamlit Cloud
def get_benchmark_path():
    # Try relative to current working directory (Streamlit Cloud)
    path1 = os.path.join("benchmark", "final_benchmark_results.json")
    if os.path.isfile(path1):
        return path1
    # Try relative to this file (local development)
    path2 = os.path.join(os.path.dirname(__file__), "..", "benchmark", "final_benchmark_results.json")
    path2 = os.path.normpath(path2)
    if os.path.isfile(path2):
        return path2
    return None

def load_benchmark():
    path = get_benchmark_path()
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading benchmark: {e}")
        return None

data = load_benchmark()

st.markdown("<p class='bench-title'>RAG Benchmark Analysis</p>", unsafe_allow_html=True)
st.markdown("<p class='bench-subtitle'>Executive Report</p>", unsafe_allow_html=True)

if not data:
    st.info("📊 **No benchmark results yet.**\n\nTo see the benchmark report:\n1. Run the benchmark locally: `python benchmark/run_benchmark.py path/to/report.pdf`\n2. Commit the generated file: `git add benchmark/final_benchmark_results.json`\n3. Push: `git push origin main`\n4. Refresh this page after Streamlit Cloud redeploys.")
    st.stop()

meta = data.get("meta", {})
stats = data.get("system_stats", {})
summary = data.get("benchmark_summary", {})
runs = data.get("runs", [])
executive = data.get("executive_summary", "")

st.markdown("<p class='bench-section'>System Stats</p>", unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Runs", stats.get("runs", "--"))
with c2:
    st.metric("Docs", stats.get("docs", "--"))
with c3:
    st.metric("Questions", stats.get("total_questions", "--"))
with c4:
    lat = stats.get("total_latency_ms")
    st.metric("Total Latency (ms)", f"{lat:,.0f}" if lat is not None else "--")
with c5:
    sim = stats.get("avg_similarity_score")
    st.metric("Avg Similarity", f"{sim:.4f}" if sim is not None else "--")

st.markdown("<p class='bench-section'>Benchmark Summary</p>", unsafe_allow_html=True)
st.write(f"**Source:** {summary.get('source_document', meta.get('source_file', '--'))}  |  **Model:** {summary.get('model_used', meta.get('model', '--'))}  |  **Status:** {summary.get('status', '--')}")

st.markdown("<p class='bench-section'>RAG Performance Report</p>", unsafe_allow_html=True)
for r in runs:
    with st.container():
        st.markdown(f"**{r.get('id', '')}** {r.get('category', '')}  \n*{r.get('question', '')}*")
        meta_parts = []
        if r.get("latency_ms") is not None:
            meta_parts.append(f"Latency: {r['latency_ms']} ms")
        if r.get("similarity_score") is not None:
            meta_parts.append(f"Similarity: {r['similarity_score']:.4f}")
        if meta_parts:
            st.caption("  |  ".join(meta_parts))
        st.markdown(f"<div class='bench-a'>{r.get('answer', 'No response.')}</div>", unsafe_allow_html=True)
        if r.get("sources"):
            with st.expander("Sources"):
                for i, s in enumerate(r["sources"], 1):
                    score_str = f"Score: {s['score']:.4f}  |  " if s.get("score") is not None else ""
                    st.text(score_str + (s.get("snippet", "")[:500] + ("..." if len(s.get("snippet", "")) > 500 else "")))
        st.divider()

st.markdown("<p class='bench-section'>Executive LLM Analysis</p>", unsafe_allow_html=True)
st.markdown(f"<div class='bench-exec'>{executive}</div>", unsafe_allow_html=True)
