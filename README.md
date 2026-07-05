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

`POST /api/index`

Fetches the transcript, chunks it with timestamp ranges, embeds each chunk, and
stores the chunks in local Chroma storage under `backend/chroma`.

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

`POST /api/search`

Searches indexed chunks for a video.

```json
{
  "video_id": "dQw4w9WgXcQ",
  "query": "main topic discussed",
  "limit": 5
}
```
