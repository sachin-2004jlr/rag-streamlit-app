"""Quick script to verify pages folder structure for Streamlit"""
import os

print("Checking pages folder structure...")
print(f"Current directory: {os.getcwd()}")
print(f"Pages folder exists: {os.path.exists('pages')}")
if os.path.exists('pages'):
    print(f"Files in pages/: {os.listdir('pages')}")
    if os.path.exists('pages/1_Benchmark_Report.py'):
        print("✓ pages/1_Benchmark_Report.py exists")
    else:
        print("✗ pages/1_Benchmark_Report.py NOT FOUND")
else:
    print("✗ pages/ folder NOT FOUND")

print(f"\nBenchmark folder exists: {os.path.exists('benchmark')}")
if os.path.exists('benchmark'):
    print(f"Files in benchmark/: {os.listdir('benchmark')}")
