# ResearchPilot AI 🔬

### AI-Powered Research Companion using RAG, Agentic AI & IBM Granite

ResearchPilot AI is an AI-powered research companion designed to help students and researchers explore, analyze, compare, and synthesize research papers from a single platform.

It allows users to upload research papers, ask questions grounded in their documents, compare papers, identify potential research gaps, explore research landscapes, and generate literature reviews.

The application is designed for integration with **IBM watsonx.ai and IBM Granite** and includes a **Demo Mode** for running the application without IBM credentials.

---

## 🚀 Key Features

### 📄 Research Paper Management
- Upload research papers in PDF format
- Extract text using PyMuPDF
- Preserve page-level information
- Automatically analyze uploaded papers

### 💬 Research Chat
- Ask questions about the research collection
- Retrieve relevant research content before generating responses
- Paper-specific and collection-wide research queries
- Source-aware research responses

### 🔎 Retrieval-Augmented Generation (RAG)
ResearchPilot uses a retrieval pipeline to ground research responses in uploaded documents.

```text
PDF
 ↓
Text Extraction
 ↓
Text Cleaning
 ↓
Chunking
 ↓
Embeddings
 ↓
FAISS / Keyword Retrieval
 ↓
Relevant Research Context
 ↓
AI Response
