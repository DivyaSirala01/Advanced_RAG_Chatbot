# ⚡ Step 7.2 — Preloading Retrievers (Optimization Proposal)

## 🎯 Objective

Improve system performance by avoiding repeated loading of retrieval components (FAISS + BM25) for every query.

---

## 🚨 Problem

In the current implementation, retrievers may be initialized or loaded during each query execution.

This leads to:
- Increased latency
- Repeated disk I/O
- Unnecessary computation overhead

---

## 💡 Proposed Solution

Preload retrievers at application startup and reuse them across all queries.

---

## 🧠 Design Approach

### Current Flow

Query
  ↓
Load FAISS + BM25
  ↓
Run Retrieval
  ↓
Generate Response

---

### Optimized Flow

Application Startup
  ↓
Load FAISS + BM25 once
  ↓
Store in memory

Query
  ↓
Use preloaded retrievers
  ↓
Run Retrieval
  ↓
Generate Response

---

## 🧩 Implementation Strategy

- Initialize retrievers in FastAPI startup event
- Store retrievers in global variables or dependency container
- Reuse retrievers across requests

---

## ⚡ Expected Improvements

| Metric        | Before        | After         |
|--------------|--------------|--------------|
| Latency      | Higher       | Lower        |
| Disk I/O     | Repeated     | Minimal      |
| Efficiency   | Lower        | Higher       |
| Scalability  | Limited      | Improved     |

---

## ⚠️ Considerations

- Retrievers should be treated as read-only
- Thread safety must be ensured
- Memory usage should be monitored

---

## 🧠 Insight

This optimization aligns with production best practices where heavy components (models, indexes, connections) are initialized once and reused.

---

## 📌 Status

🚧 Not implemented (design-level optimization)
