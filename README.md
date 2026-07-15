# Explainable RAG Banking Agent

A retrieval-augmented agent that answers questions about Central Bank of Egypt (CBE) consumer protection circulars — in **Arabic or English, matching whatever language the user asks in** — while showing exactly which source text it used and how confident it is in the answer.

Built as a two-week applied project to practice explainable AI, LangGraph orchestration, and RAG evaluation on real regulatory documents.

## Why this exists

Most RAG demos answer confidently and never show their work. This project treats "why did the agent say that" as an explainability problem — the same lens as SHAP/LIME, applied to retrieval instead of tabular features. Every answer is grounded in a specific source chunk, scored for how well-supported it actually is, and escalated to a human-review flag if the system isn't confident.

## Architecture

```
User question (AR or EN)
        │
        ▼
   ┌─────────┐
   │ retrieve │  multilingual embedding search over CBE circular chunks
   └────┬────┘
        ▼
   ┌─────────┐
   │  answer  │  LLM generates grounded answer, matches input language
   └────┬────┘
        ▼
   ┌─────────┐
   │  verify  │  groundedness/confidence check against retrieved chunks
   └────┬────┘
        ▼
  pass ──────── escalate (low confidence → flagged for human review)
```

## Repo structure

```
explainable-rag-banking-agent/
├── data/
│   ├── raw/                  # original downloaded PDFs (not committed if large — see .gitignore)
│   └── processed/            # cleaned text + chunked JSON/parquet ready for embedding
├── src/
│   ├── ingestion/            # PDF extraction, cleaning, chunking
│   ├── rag/                  # embedding, vector store, retrieval logic
│   ├── graph/                # LangGraph nodes: retrieve / answer / verify / escalate
│   └── eval/                 # eval question set + scoring scripts
├── app/                      # Streamlit/Gradio front end
├── notebooks/                # exploratory notebooks (data checks, quick experiments)
├── tests/                    # unit tests for ingestion + retrieval
├── docs/                     # architecture notes, write-up, screenshots for README
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

```bash
git clone <your-repo-url>
cd explainable-rag-banking-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
```

## Usage

```bash
# 1. Extract + chunk raw PDFs in data/raw/
python -m src.ingestion.build_corpus

# 2. Embed chunks and build the vector store
python -m src.rag.build_index

# 3. Run the app
streamlit run app/main.py
```

## Data source

Public circulars from the [Central Bank of Egypt](https://www.cbe.org.eg/en/laws-regulations/regulations/circulars), Consumer Protection category. Documents are official public regulatory text; this project is an independent educational/portfolio project and is not affiliated with or endorsed by the CBE.

## Status

🚧 Work in progress — built as a 2-week applied learning project (see `docs/`).

## License

MIT — see `LICENSE`.
