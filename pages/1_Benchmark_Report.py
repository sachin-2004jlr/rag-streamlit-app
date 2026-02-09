"""
Benchmark Report Page for RAG System
Displays benchmark analysis results from final_benchmark_results.json
"""
import streamlit as st
import json
import os

# Page config
st.set_page_config(
    page_title="Benchmark Report | RAG", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Dark theme CSS matching main app
st.markdown("""
<style>
.stApp { background-color: #0e1117; }
.bench-title { 
    font-family: 'Inter', sans-serif; 
    color: #f3f4f6; 
    font-weight: 700; 
    letter-spacing: -0.02em; 
    margin-bottom: 0.25rem; 
    font-size: 2rem;
}
.bench-subtitle { 
    color: #6b7280; 
    font-size: 0.85rem; 
    margin-bottom: 1.5rem; 
}
.bench-section { 
    font-size: 0.7rem; 
    font-weight: 600; 
    letter-spacing: 0.15em; 
    text-transform: uppercase; 
    color: #6b7280; 
    margin: 1.5rem 0 0.75rem; 
    border-bottom: 1px solid #1f2937; 
    padding-bottom: 0.5rem; 
}
.bench-exec { 
    border-left: 4px solid #4a9eff; 
    padding-left: 1rem; 
    color: #9aa0a6; 
    font-size: 0.95rem; 
    line-height: 1.7; 
}
</style>
""", unsafe_allow_html=True)

def find_benchmark_json():
    """Find benchmark JSON file - works on both local and Streamlit Cloud"""
    # Try multiple paths
    paths_to_try = [
        "benchmark/final_benchmark_results.json",  # Streamlit Cloud (from repo root)
        os.path.join("benchmark", "final_benchmark_results.json"),  # Cross-platform
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "benchmark", "final_benchmark_results.json")),  # Local dev
    ]
    
    for path in paths_to_try:
        if os.path.isfile(path):
            return path
    return None

def load_benchmark_data():
    """Load benchmark JSON data"""
    json_path = find_benchmark_json()
    if not json_path:
        return None
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading benchmark data: {str(e)}")
        return None

# Load data
benchmark_data = load_benchmark_data()

# Header
st.markdown("<p class='bench-title'>RAG Benchmark Analysis</p>", unsafe_allow_html=True)
st.markdown("<p class='bench-subtitle'>Executive Report</p>", unsafe_allow_html=True)

# Show content or empty state
if not benchmark_data:
    st.info("**No benchmark results yet.**\n\nTo see the benchmark report:\n1. Run the benchmark locally: `python benchmark/run_benchmark.py path/to/report.pdf`\n2. Commit the generated file: `git add benchmark/final_benchmark_results.json`\n3. Push: `git push origin main`\n4. Refresh this page after Streamlit Cloud redeploys.")
    
    # Show empty state structure
    st.markdown("<p class='bench-section'>System Stats</p>", unsafe_allow_html=True)
    st.write("No data available.")
    
    st.markdown("<p class='bench-section'>RAG Performance Report</p>", unsafe_allow_html=True)
    st.write("No questions evaluated yet.")
    
    st.markdown("<p class='bench-section'>Executive LLM Analysis</p>", unsafe_allow_html=True)
    st.write("Benchmark not yet executed.")
else:
    # Extract data
    meta = benchmark_data.get("meta", {})
    stats = benchmark_data.get("system_stats", {})
    summary = benchmark_data.get("benchmark_summary", {})
    runs = benchmark_data.get("runs", [])
    executive = benchmark_data.get("executive_summary", "")

    # System Stats
    st.markdown("<p class='bench-section'>System Stats</p>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Runs", stats.get("runs", "--"))
    with col2:
        st.metric("Docs", stats.get("docs", "--"))
    with col3:
        st.metric("Questions", stats.get("total_questions", "--"))
    with col4:
        lat = stats.get("total_latency_ms")
        st.metric("Total Latency (ms)", f"{lat:,.0f}" if lat is not None else "--")
    with col5:
        sim = stats.get("avg_similarity_score")
        st.metric("Avg Similarity", f"{sim:.4f}" if sim is not None else "--")

    # Benchmark Summary
    st.markdown("<p class='bench-section'>Benchmark Summary</p>", unsafe_allow_html=True)
    source = summary.get('source_document', meta.get('source_file', '--'))
    model = summary.get('model_used', meta.get('model', '--'))
    status = summary.get('status', '--')
    st.write(f"**Source:** {source}  |  **Model:** {model}  |  **Status:** {status}")

    # Performance Report
    st.markdown("<p class='bench-section'>RAG Performance Report</p>", unsafe_allow_html=True)
    
    if not runs:
        st.write("No runs recorded.")
    else:
        for run in runs:
            with st.container():
                q_id = run.get('id', '')
                category = run.get('category', '')
                question = run.get('question', '')
                answer = run.get('answer', 'No response.')
                
                st.markdown(f"**{q_id}** {category}")
                st.markdown(f"*{question}*")
                
                # Metadata
                meta_parts = []
                if run.get("latency_ms") is not None:
                    meta_parts.append(f"Latency: {run['latency_ms']} ms")
                if run.get("similarity_score") is not None:
                    meta_parts.append(f"Similarity: {run['similarity_score']:.4f}")
                if meta_parts:
                    st.caption("  |  ".join(meta_parts))
                
                # Answer
                st.markdown(f"<div style='color: #9aa0a6; font-size: 0.9rem; line-height: 1.6; margin: 0.5rem 0;'>{answer}</div>", unsafe_allow_html=True)
                
                # Sources
                if run.get("sources"):
                    with st.expander("View Sources"):
                        for i, source in enumerate(run["sources"], 1):
                            score_str = ""
                            if source.get("score") is not None:
                                score_str = f"Score: {source['score']:.4f}  |  "
                            snippet = source.get("snippet", "")
                            if len(snippet) > 500:
                                snippet = snippet[:500] + "..."
                            st.text(f"{score_str}{snippet}")
                
                st.divider()

    # Executive Summary
    st.markdown("<p class='bench-section'>Executive LLM Analysis</p>", unsafe_allow_html=True)
    st.markdown(f"<div class='bench-exec'>{executive}</div>", unsafe_allow_html=True)
