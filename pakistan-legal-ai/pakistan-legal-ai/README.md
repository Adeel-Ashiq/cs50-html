# Pakistan Legal AI Research System

**AI-Powered Legal Research and Case Recommendation System for Pakistan**  
Final Year Project (FYP) Demo

## Features

- Natural language query (Urdu + English)
- Relevant **Constitution Articles**
- Relevant **Acts & Sections**
- Similar past **court judgments** with summary, court, year, judges
- **Suggested legal arguments** with references
- Clean modern React frontend
- FastAPI + ChromaDB + Sentence Transformers RAG backend

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React + Vite                        |
| Backend    | FastAPI (Python)                    |
| Vector DB  | ChromaDB                            |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Data       | Sample Constitution + Acts + Judgments (JSON) |

## Project Structure

```
pakistan-legal-ai/
├── backend/
│   ├── app/
│   │   ├── core/          # Config
│   │   ├── models/        # Pydantic schemas
│   │   ├── routers/       # API routes
│   │   ├── services/      # RAG service
│   │   └── main.py
│   ├── sample_data/       # Constitution, Acts, Judgments
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
└── README.md
```

## How to Run

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Backend will start at: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

First run will download the embedding model and build the vector index (may take 1-2 minutes).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will start at: **http://localhost:5173**

## Sample Queries

- Do bhaiyon ke darmiyan zameen ki warasat ka dispute hai
- Sister ko inheritance se exclude karne ki koshish ki gai hai oral gift ke zariye
- Mutation mein ghalat entry hai, kaise challenge karein?
- Co-sharer ne exclusive possession le liya hai, partition ka suit maintainable hai?
- Predeceased son ke children ka hissa kya hoga under MFLO Section 4?

## Important Notes

- This is a **demo with sample data** only.
- Real judgments are illustrative (based on common legal principles).
- Always verify with original sources (PLD, SCMR, CLC, Pakistan Code etc.).
- Not a substitute for professional legal advice.

## Extending the Project

1. Add more judgments in `backend/sample_data/judgments.json`
2. Add more Acts in `acts.json`
3. Re-run backend (or delete `backend/chroma_db` folder to rebuild index)
4. For production: replace sample data with real scraped/cleaned judgments + better LLM for argument generation

## License

For educational / FYP purposes only.
