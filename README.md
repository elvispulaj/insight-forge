# 🔥 InsightForge — AI-Powered Business Intelligence Assistant

> Transform your business data into actionable insights with AI-powered analysis, natural language Q&A, and smart visualizations.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)

---

## 📖 Overview

**InsightForge** is an innovative Business Intelligence Assistant that leverages **LangChain**, **Retrieval-Augmented Generation (RAG)**, and **Large Language Models (LLMs)** to help organizations of any size transform raw data into strategic intelligence.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🔍 **AI Analysis** | Comprehensive data analysis identifying trends, patterns, anomalies and delivering actionable recommendations |
| 💬 **Natural Language Q&A** | Ask questions about your data in plain English; RAG-enhanced context ensures accurate, grounded answers |
| 📊 **Smart Visualizations** | Auto-generated interactive Plotly charts with custom chart builder and AI-suggested visualizations |
| 📄 **Document Intelligence** | Ingest PDFs, DOCX, and text files into a searchable RAG knowledge base |
| 🧠 **RAG Knowledge Base** | FAISS vector store with HuggingFace embeddings for context-aware retrieval |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                      │
│  ┌───────┐ ┌──────────┐ ┌─────┐ ┌──────┐ ┌──────┐ │
│  │Dashboard│ │AI Analysis│ │ Q&A │ │ Viz  │ │ Docs │ │
│  └───┬───┘ └────┬─────┘ └──┬──┘ └──┬───┘ └──┬───┘ │
│      │          │           │       │        │      │
│  ┌───▼──────────▼───────────▼───────▼────────▼───┐  │
│  │              Session State Manager            │  │
│  └───────────────────┬───────────────────────────┘  │
└──────────────────────┼──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼─────┐
   │  LLM    │   │    RAG    │  │  Data    │
   │  Engine │   │   Engine  │  │  Loader  │
   │(LangChain)│ │(FAISS+HF) │  │(Pandas)  │
   └────┬────┘   └─────┬─────┘  └────┬─────┘
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼─────┐
   │ OpenAI  │   │  Vector   │  │  Files   │
   │  API    │   │   Store   │  │ CSV/XLSX │
   └─────────┘   └───────────┘  │ PDF/DOCX │
                                └──────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **LLM** | LangChain + OpenAI (GPT-4o-mini) | Natural language analysis & generation |
| **RAG** | FAISS + HuggingFace Embeddings | Context-aware document retrieval |
| **Data** | Pandas + NumPy | Data processing & statistical analysis |
| **Visualization** | Plotly + Matplotlib + Seaborn | Interactive & static charts |
| **Documents** | PyPDF, python-docx | PDF & DOCX parsing |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone or navigate to the project directory:**

```bash
cd "Antigravity InsightForge"
```

2. **Create and activate a virtual environment (recommended):**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure your API key:**

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

Or simply enter it in the sidebar when the app launches.

5. **Run the application:**

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📁 Project Structure

```
InsightForge/
├── app.py                 # Main Streamlit application (entry point)
├── config.py              # Centralized configuration
├── data_loader.py         # Multi-format data ingestion & profiling
├── rag_engine.py          # RAG pipeline (FAISS + embeddings)
├── llm_engine.py          # LLM analysis engine (LangChain + OpenAI)
├── visualizer.py          # Chart generation (Plotly)
├── sample_data.py         # Sample dataset generator
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── data/
│   ├── uploads/           # User-uploaded files
│   ├── vector_store/      # Persisted FAISS indices
│   └── sample/            # Generated sample datasets
└── README.md
```

---

## 🎯 Usage Guide

### 1. Dashboard
- View KPI cards, data previews, and auto-generated charts
- Quick overview of your dataset's shape and quality

### 2. AI Analysis
- **Comprehensive Analysis**: One-click full analysis with executive summary, trends, anomalies, and recommendations
- **Custom Analysis**: Describe a specific analysis you need

### 3. Ask Questions (Q&A)
- Chat with your data using natural language
- RAG-enhanced answers grounded in your actual data
- Suggested starter questions for quick insights

### 4. Visualizations
- **Auto-Generated**: AI picks the best charts for your data
- **Custom Charts**: Build bar, line, scatter, pie, box, histogram, and heatmap charts
- **AI Suggestions**: Get LLM-powered visualization recommendations

### 5. Documents
- View uploaded document content
- Test RAG retrieval with custom queries
- Monitor knowledge base status

---

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Your OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace embedding model |
| `CHUNK_SIZE` | `1000` | Text chunk size for RAG |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `MAX_UPLOAD_SIZE_MB` | `200` | Maximum file upload size |

---

## 📊 Supported File Formats

| Format | Type | Library |
|--------|------|---------|
| `.csv` | Tabular | Pandas |
| `.xlsx` / `.xls` | Tabular | openpyxl |
| `.json` | Tabular | Pandas |
| `.pdf` | Document | PyPDF |
| `.docx` | Document | python-docx |
| `.txt` | Document | Built-in |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is developed as a capstone project for the Purdue GenAI program.

---

<p align="center">
  Built with ❤️ using <strong>LangChain</strong>, <strong>RAG</strong>, and <strong>OpenAI</strong>
</p>
