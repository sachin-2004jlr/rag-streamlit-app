import os
import json
import sys
from llama_index.core import SimpleDirectoryReader, Settings
from llama_index.llms.groq import Groq
from dotenv import load_dotenv

# Load environment variables (Force reload)
load_dotenv(override=True)

def generate_questions(pdf_path, output_path, num_questions=20):
    """
    Generates Q&A pairs from the provided PDF using Llama 3.3.
    """
    print(f"Starting generation process...", flush=True)
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}", flush=True)
        return

    print(f"Loading PDF from {pdf_path}...", flush=True)
    try:
        reader = SimpleDirectoryReader(input_files=[pdf_path])
        documents = reader.load_data()
        text_content = ""
        for doc in documents:
            text_content += doc.text + "\n"
        print(f"Loaded {len(documents)} documents. Total text length: {len(text_content)}", flush=True)
    except Exception as e:
        print(f"Error loading PDF: {e}", flush=True)
        return

    # Truncate text content to fit within context window if necessary
    max_chars = 30000 
    if len(text_content) > max_chars:
        print(f"Text content too long ({len(text_content)} chars). Truncating to {max_chars} chars.", flush=True)
        text_content = text_content[:max_chars]

    print("Initializing Groq LLM...", flush=True)
    try:
        llm = Groq(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
        Settings.llm = llm
    except Exception as e:
        print(f"Error initializing LLM: {e}", flush=True)
        return

    prompt = f"""
    You are an expert at creating benchmark datasets for RAG systems.
    
    Given the following text from a research paper, generate {num_questions} diverse verification questions 
    and their corresponding correct answers.
    
    The questions should vary in difficulty:
    - Factual retrieval
    - Summarization
    - Reasoning
    
    Output the result STRICTLY as a JSON array of objects, where each object has:
    - "question": The generated question.
    - "ground_truth": The correct answer based entirely on the text.
    - "type": One of "factual", "summarization", "reasoning".
    
    Do not include any markdown formatting. Just the raw JSON string.
    
    TEXT CONTENT:
    {text_content}
    """

    print("Generating Q&A pairs...", flush=True)
    try:
        response = llm.complete(prompt)
        print("Response received.", flush=True)
    except Exception as e:
        print(f"Error generating Q&A: {e}", flush=True)
        return
    
    try:
        # Clean up response if it contains markdown code blocks
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        qa_pairs = json.loads(response_text)
        
        # Save to file
        with open(output_path, "w") as f:
            json.dump(qa_pairs, f, indent=4)
            
        print(f"Successfully generated {len(qa_pairs)} Q&A pairs to {output_path}", flush=True)
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}", flush=True)
        print("Raw response:", response.text, flush=True)
    except Exception as e:
        print(f"An error occurred: {e}", flush=True)

if __name__ == "__main__":
    pdf_file = os.path.join("benchmark_data", "Dr.R.Praba-StudyonMLAlgorithms.pdf")
    output_file = os.path.join("benchmark_data", "test_set.json")
    generate_questions(pdf_file, output_file)
