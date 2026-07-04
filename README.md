# YouTube Chat

Local MVP for fetching and displaying timestamped YouTube transcripts.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

## API

`POST /api/transcript`

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```
