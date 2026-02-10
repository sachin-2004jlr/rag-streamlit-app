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
    "Mixtral 8x7b": "mixtral-8x7b-32768",
    "Gemma 2 9b": "gemma2-9b-it"
}

DB_PATH = os.path.join("temp_data", "benchmark_db") 
PDF_PATH = os.path.join("benchmark_data", "Dr.R.Praba-StudyonMLAlgorithms.pdf")
DATASET_PATH = os.path.join("benchmark_data", "test_set.json")
RESULTS_PATH = os.path.join("benchmark_data", "results.json")

def setup_rag_engine(db_path):
    print("Setting up RAG engine...")
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Settings.embed_model = embed_model
    
    if not os.path.exists(db_path):
        print("Database not found. Creating new vector store...")
        try:
            # Import strictly inside function to avoid issues if module missing (though we fixed it)
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
            
    chroma_client = chromadb.PersistentClient(path=db_path)
    chroma_collection = chroma_client.get_or_create_collection("benchmark_data")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    return index

def evaluate_answer(question, ground_truth, prediction, model_name):
    # Judge with a strong model
    # Judge with a faster model to avoid rate limits
    judge_llm = Groq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
    
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
        txt = response.text.strip()
        if txt.startswith("```json"): txt = txt[7:]
        if txt.endswith("```"): txt = txt[:-3]
        return json.loads(txt)
    except Exception as e:
        return {"relevance_score": 0, "accuracy_score": 0, "explanation": f"Evaluation failed: {str(e)}"}

def run_benchmark():
    if not os.path.exists(DATASET_PATH):
        print("Dataset not found. Run generate_dataset.py first.")
        return

    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    index = setup_rag_engine(DB_PATH)
    if not index:
        return

    # Load existing results to resume
    results = []
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, "r") as f:
                results = json.load(f)
            print(f"Resuming benchmark. Loaded {len(results)} existing results.")
        except:
            print("Could not load existing results. Starting fresh.")
    
    # Create a map of processed items for fast lookup and status check
    processed = {}
    for r in results:
        processed[(r["model"], r["question"])] = r

    for name, model_id in MODELS.items():
        print(f"\n--- Testing Model: {name} ({model_id}) ---")
        
        try:
            llm = Groq(model=model_id, api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)
            query_engine = index.as_query_engine(llm=llm, similarity_top_k=3)
            
            for i, item in enumerate(dataset):
                question = item["question"]
                ground_truth = item["ground_truth"]
                
                # Check if already done AND evaluation succeeded
                key = (name, question)
                if key in processed:
                    prev_result = processed[key]
                    if prev_result.get("explanation") != "Evaluation failed" and "Evaluation failed" not in str(prev_result.get("explanation", "")):
                        print(f"Skipping Q{i+1} (already done successfully)")
                        continue
                    else:
                        print(f"Retrying Q{i+1} (previous evaluation failed)...")
                        # If we have a prediction but eval failed, we could just re-eval, but simpler to re-run or re-use prediction.
                        # For simplicity, let's re-use prediction if available to save RAG tokens/latency
                        prediction = prev_result.get("prediction")
                        latency = prev_result.get("latency", 0)
                        
                        if prediction:
                            print("  Re-using existing prediction, running evaluation only...")
                            eval_metrics = evaluate_answer(question, ground_truth, prediction, name)
                            # Update result in list
                            # Find index of this result
                            for idx, r in enumerate(results):
                                if r["model"] == name and r["question"] == question:
                                    results[idx].update(eval_metrics)
                                    break
                            
                            with open(RESULTS_PATH, "w") as f:
                                json.dump(results, f, indent=4)
                            time.sleep(2)
                            continue

                print(f"Processing Q{i+1}: {question[:50]}...")
                
                try:
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
                    processed[(name, question)] = results[-1]
                    
                    # Save immediately
                    with open(RESULTS_PATH, "w") as f:
                        json.dump(results, f, indent=4)
                    
                    # Rate limit handling
                    time.sleep(5) 
                    
                except Exception as e:
                    print(f"Error processing Q{i+1}: {e}")
                    time.sleep(10) # Wait longer on error

        except Exception as e:
            print(f"Failed to run model {name}: {e}")

    print(f"\nBenchmark complete. Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    run_benchmark()
