# 🚀 STEP 1 — Build the Absolute Minimum Working System (Foundation)

Before advanced RAG, you need a **working vertical slice**:

👉 **Goal of Step 1:**

> A simple chatbot that answers questions from your documents using basic RAG.

No roles, no hybrid retrieval, no reasoning yet.

---

## 🎯 What You Will Build in Step 1

A pipeline like this:

```
User Question
   ↓
Embed Query
   ↓
Retrieve Documents (FAISS)
   ↓
Send Context + Query to LLM
   ↓
Get Answer
```

---

## 🧱 What You Need to Create (Core layout)

Start small. Don’t touch full architecture yet.

```
app/
 ├── main.py
 ├── core/pipeline.py
 ├── retrieval/vector_store.py
 ├── generation/generator.py

scripts/
 ├── ingest_data.py
 └── run_all.py
```

---

## ⚙️ STEP 1.1 — Setup Environment

Install basics:

```bash
pip install openai langchain faiss-cpu streamlit fastapi uvicorn
```

Create `.env`:

```env
OPENAI_API_KEY=your_key_here
```

---

## 📥 STEP 1.2 — Ingest Your Data (VERY IMPORTANT)

----> scripts/ingest.py
👉 This will:

* Load documents
* Chunk them
* Create embeddings
* Store in FAISS

👉 Run this:

```bash
python scripts/ingest_data.py
```

---

## 🔍 STEP 1.3 — Retrieval Layer

Create:

```bash
app/retrieval/vector_store.py
```

## 🧠 STEP 1.4 — Generation Layer

Create:

```bash
app/generation/generator.py
```

---

## 🔗 STEP 1.5 — Pipeline (CORE)

Create:

```bash
app/core/pipeline.py
```
---

## 🌐 STEP 1.6 — FastAPI Endpoint

Create:

```bash
app/main.py
```

```python
from fastapi import FastAPI
from pydantic import BaseModel
from app.core.pipeline import run_pipeline

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/chat")
def chat(request: QueryRequest):
    response = run_pipeline(request.query)
    return {"answer": response}
```

Run:

```bash
uvicorn app.main:app --reload
```

---

## 🖥️ STEP 1.7 — (Optional but Recommended) Streamlit UI

```bash
ui/app.py
```
Run:

```bash
streamlit run ui/app.py
```

---

## ▶️ STEP 1.8 — `scripts/run_all.py` (one-command dev launcher)

Create:

```bash
scripts/run_all.py
```

This script wires the whole local dev flow together:

* **Checks** whether the FAISS index folder `db/faiss_index` exists.
* **Ingests** by running `scripts/ingest_data.py` if the index is missing; otherwise skips ingestion.
* **Starts FastAPI** with `uvicorn app.main:app --reload`.
* **Starts Streamlit** with `streamlit run ui/app.py`.
* **Waits** on both child processes; on **Ctrl+C**, terminates both cleanly.

Run everything from the project root:

```bash
python scripts/run_all.py
```
---

# ✅ What You Should Have After Step 1

* ✅ Working chatbot
* ✅ Uses your own data
* ✅ End-to-end pipeline
* ✅ FastAPI + Streamlit connected
* ✅ Optional `scripts/run_all.py` to ingest (if needed), then launch API + UI

---

# ⚠️ Common Mistakes (Avoid These)

* ❌ Trying hybrid retrieval now
* ❌ Adding roles too early
* ❌ Overengineering chunking
* ❌ Using LangGraph yet

👉 Right now you just need:
**ONE working pipeline**

---

# 🚀 After You Finish This

Next step will be:

👉 **STEP 2 — Role-Based RAG (RAG vs Agentic split)**

* Separate knowledge bases
* Routing logic
* Context filtering

---


# Summary: Build a basic end-to-end RAG chatbot using your own data

1. Data Layer
    * Created RAG and Agentic text datasets
    * Acts as the knowledge base

2. Ingestion Pipeline
    * Loaded raw text data
    * Split into smaller chunks
    * Converted chunks into embeddings
    * Stored embeddings in FAISS vector database

3. Retrieval Layer
    * Converted user query into embedding
    * Performed similarity search in FAISS
    * Retrieved top relevant chunks

4. Generation Layer
    * Sent retrieved context + query to LLM
    * Generated grounded response

5. Pipeline (Orchestration)
    * Connected retrieval → context building → generation
    * Acts as the main execution flow

6. API Layer (FastAPI)
    * Exposed chatbot as a `/chat` endpoint
    * Handles request → response flow

7. UI Layer (Streamlit)
    * Simple chatbot interface
    * Sends query to backend and displays response

8. Runner Script
    * Single command to:
        * Run ingestion (if needed)
        * Start backend
        * Start UI

##End-to-End Flow
User → UI → API → Pipeline → Retrieval → LLM → Response

# Key Outcome - Working RAG system with:
  * Custom data
  * Semantic retrieval
  * Grounded answers
  * Full stack (UI + API)

-----
## 🧠 Step 1 — Tech Components (“Tags”) Used

* **TextLoader** → for loading raw text files

* **RecursiveCharacterTextSplitter** → for chunking large text into smaller pieces

* **OpenAIEmbeddings** → for converting text into vector embeddings

* **FAISS** → vector database for storing and retrieving embeddings

* **Retriever (`as_retriever`)** → for semantic search over FAISS

* **ChatOpenAI (LLM)** → for generating final responses

* **Custom Pipeline Function** → to orchestrate retrieval + generation

* **FastAPI** → to expose `/chat` API endpoint

* **Pydantic** → for request/response schema validation

* **Streamlit** → for building chatbot UI

* **Requests (HTTP call)** → to connect UI → backend

* **dotenv (`load_dotenv`)** → to manage API keys securely

* **uv / virtual environment** → for dependency and environment management


> Data Loader → Chunker → Embeddings → FAISS → Retriever → LLM → Pipeline → API → UI
