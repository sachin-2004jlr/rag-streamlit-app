import streamlit as st
import json
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Benchmark Analysis", layout="wide")

st.title("RAG Benchmark Analysis")
st.markdown("### Performance Comparison of 5 LLM Models")

RESULTS_PATH = os.path.join("benchmark_data", "results.json")

if not os.path.exists(RESULTS_PATH):
    st.warning("Benchmark results not found. Please run the benchmark script first.")
    st.stop()

with open(RESULTS_PATH, "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# KPI Metrics
st.markdown("#### Aggregate Metrics")
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

avg_latency = df.groupby("model")["latency"].mean().sort_values()
avg_relevance = df.groupby("model")["relevance_score"].mean().sort_values(ascending=False)
avg_accuracy = df.groupby("model")["accuracy_score"].mean().sort_values(ascending=False)

with kpi_col1:
    st.subheader("Fastest Model")
    st.metric(label="Latency (s)", value=f"{avg_latency.iloc[0]:.2f}", delta=avg_latency.index[0])

with kpi_col2:
    st.subheader("Most Relevant")
    st.metric(label="Relevance (0-10)", value=f"{avg_relevance.iloc[0]:.2f}", delta=avg_relevance.index[0])

with kpi_col3:
    st.subheader("Most Accurate")
    st.metric(label="Accuracy (0-10)", value=f"{avg_accuracy.iloc[0]:.2f}", delta=avg_accuracy.index[0])

st.divider()

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Latency Comparison")
    fig_lat = px.bar(avg_latency, x=avg_latency.index, y="latency", color=avg_latency.index, title="Average Latency (seconds)")
    st.plotly_chart(fig_lat, use_container_width=True)

with chart_col2:
    st.subheader("Quality Comparison")
    # Melt for grouped bar chart
    quality_df = df.groupby("model")[["relevance_score", "accuracy_score"]].mean().reset_index()
    quality_melt = quality_df.melt(id_vars="model", var_name="Metric", value_name="Score")
    fig_qual = px.bar(quality_melt, x="model", y="Score", color="Metric", barmode="group", title="Quality Scores (0-10)")
    st.plotly_chart(fig_qual, use_container_width=True)

st.divider()

# Detailed View
st.subheader("Detailed Analysis")
model_filter = st.multiselect("Filter by Model", options=df["model"].unique(), default=df["model"].unique())

filtered_df = df[df["model"].isin(model_filter)]
st.dataframe(filtered_df, use_container_width=True)

# Expander for individual Q&A
with st.expander("View Individual Q&A Pairs"):
    for i, row in filtered_df.iterrows():
        st.markdown(f"**Q:** {row['question']}")
        st.markdown(f"**Ground Truth:** {row['ground_truth']}")
        st.markdown(f"**Model ({row['model']}):** {row['prediction']}")
        st.markdown(f"*Scores -> Relevance: {row['relevance_score']}, Accuracy: {row['accuracy_score']}*")
        st.divider()
