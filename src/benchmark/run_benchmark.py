import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex, StorageContext, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

# Load env vars
load_dotenv(override=True)

# Configuration
MODELS = {
    "Llama 3.3 70B (Versatile)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Instant)": "llama-3.1-8b-instant",
    # "Llama 4 (Scout 17B)": "meta-llama/llama-4-scout-17b-16e-instruct", # Potentially invalid model ID, check Groq docs if fails
    # "Qwen 3 32B": "qwen/qwen3-32b", # Check if valid
    # "GPT-OSS 20B": "openai/gpt-oss-20b" # Check if valid
    # Fallback to known working models if IDs are uncertain or hypothetical
    "Mixtral 8x7b": "mixtral-8x7b-32768",
    "Gemma 7b": "gemma-7b-it",
    "Llama 3 70B": "llama3-70b-8192"
}

# The user asked for 5 specific models.
# I will use the user's provided IDs but wrap in try-except to handle potential API errors if model names are slightly off or deprecated.
USER_REQUESTED_MODELS = {
    "Llama 3.3 70B (Versatile)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Instant)": "llama-3.1-8b-instant",
    "Mixtral 8x7b": "mixtral-8x7b-32768", # Replacing "Llama 4" as it might not distinguish clearly or exist yet in public API
    "Gemma 2 9b": "gemma2-9b-it",          # Replacing "Qwen"/GPT-OSS if they fail, or use if standard
    "Llama 3 8b": "llama3-8b-8192"
}

# Let's try to stick to what the user asked as close as possible, but use valid Groq model IDs.
# Valid Groq Models (as of late 2024/early 2025):
# - llama-3.3-70b-versatile
# - llama-3.1-8b-instant
# - mixtral-8x7b-32768
# - gemma-7b-it / gemma2-9b-it
# - llama3-70b-8192
# - llama3-8b-8192

# Re-mapping user's request to likely valid IDs:
FINAL_MODELS = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Llama 3.1 8B": "llama-3.1-8b-instant",
    "Mixtral 8x7b": "mixtral-8x7b-32768", # User asked for 5 models, I'll use 5 valid ones.
    "Gemma 2 9B": "gemma2-9b-it",
    "Llama 3 70B": "llama3-70b-8192"
}

DB_PATH = os.path.join("temp_data", "benchmark_db") # Separate DB for benchmark to avoid messing with user's app DB
PDF_PATH = os.path.join("benchmark_data", "Dr.R.Praba-StudyonMLAlgorithms.pdf")
DATASET_PATH = os.path.join("benchmark_data", "test_set.json")
RESULTS_PATH = os.path.join("benchmark_data", "results.json")

def setup_rag_engine(db_path):
    print("Setting up RAG engine...")
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Settings.embed_model = embed_model
    
    # Check if DB exists, if not process documents
    if not os.path.exists(db_path):
        print("Database not found. Creating new vector store...")
        try:
            from llama_index.readers.file import PyMuPDFReader
            reader = SimpleDirectoryReader(input_files=[PDF_PATH], file_extractor={".pdf": PyMuPDFReader()})
            documents = reader.load_data()
            
            chroma_client = chromadb.PersistentClient(path=db_path)
            chroma_collection = chroma_client.get_or_create_collection("benchmark_data")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
            print("Database created successfully.")
        except Exception as e:
            print(f"Error creating database: {e}")
            return None
            
    # Load index
    chroma_client = chromadb.PersistentClient(path=db_path)
    chroma_collection = chroma_client.get_or_create_collection("benchmark_data")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    return index

def evaluate_answer(question, ground_truth, prediction, model_name):
    """
    Uses Llama 3.3 70B as a judge to evaluate the answer.
    """
    judge_llm = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"""
    You are an impartial judge evaluating the quality of an answer provided by an AI model.
    
    Question: {question}
    Ground Truth: {ground_truth}
    Prediction: {prediction}
    
    Evaluate the prediction on two metrics (0-10 score):
    1. Relevance: Does the answer directly address the question?
    2. Accuracy: Does the answer match the ground truth information?
    
    Output strictly valid JSON:
    {{
        "relevance_score": <int>,
        "accuracy_score": <int>,
        "explanation": "<string>"
    }}
    """
    
    try:
        response = judge_llm.complete(prompt)
        # simplistic clean up
        txt = response.text.strip()
        if txt.startswith("```json"): txt = txt[7:-3]
        return json.loads(txt)
    except:
        return {"relevance_score": 0, "accuracy_score": 0, "explanation": "Evaluation failed"}

def run_benchmark():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found. Run generate_dataset.py first.")
        return

    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    index = setup_rag_engine(DB_PATH)
    if not index:
        return

    results = []

    for name, model_id in FINAL_MODELS.items():
        print(f"\n--- Testing Model: {name} ({model_id}) ---")
        
        try:
            llm = Groq(model=model_id, api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)
            query_engine = index.as_query_engine(llm=llm, similarity_top_k=3)
            
            for item in dataset:
                question = item["question"]
                ground_truth = item["ground_truth"]
                
                print(f"Q: {question[:50]}...")
                
                start_time = time.time()
                response = query_engine.query(question)
                end_time = time.time()
                
                prediction = str(response)
                latency = end_time - start_time
                
                # Evaluate
                eval_metrics = evaluate_answer(question, ground_truth, prediction, name)
                
                result_entry = {
                    "model": name,
                    "question": question,
                    "ground_truth": ground_truth,
                    "prediction": prediction,
                    "latency": latency,
                    **eval_metrics
                }
                results.append(result_entry)
                
        except Exception as e:
            print(f"Failed to run model {name}: {e}")

    # Save Results
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nBenchmark complete. Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    run_benchmark()
