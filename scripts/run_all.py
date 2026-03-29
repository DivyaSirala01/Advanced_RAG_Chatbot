import os
import subprocess
import sys

def _indexes_ready() -> bool:
    return os.path.exists("db/faiss_index_rag") and os.path.exists(
        "db/faiss_index_agentic"
    )


def run_ingestion():
    print("🔄 Running ingestion pipeline...")
    subprocess.run([sys.executable, "app/ingestion/ingest_data.py"], check=True)


def start_fastapi():
    print("🚀 Starting FastAPI server...")
    return subprocess.Popen(
        ["uvicorn", "app.main:app", "--reload"]
    )


def start_streamlit():
    print("🎨 Starting Streamlit UI...")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/app.py"]
    )


def main():
    # Step 1: Check if vector DBs exist
    if not _indexes_ready():
        print("⚠️ FAISS indexes not found (need RAG + Agentic).")
        run_ingestion()
    else:
        print("✅ FAISS indexes found. Skipping ingestion.")

    # Step 2: Start services
    fastapi_process = start_fastapi()
    streamlit_process = start_streamlit()

    try:
        fastapi_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        fastapi_process.terminate()
        streamlit_process.terminate()


if __name__ == "__main__":
    main()