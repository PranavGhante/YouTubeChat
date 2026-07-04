import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://localhost:8000/api/transcript";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [videoId, setVideoId] = useState("");
  const [transcript, setTranscript] = useState([]);

  async function fetchTranscript(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setVideoId("");
    setTranscript([]);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not fetch transcript.");
      }

      setVideoId(data.video_id);
      setTranscript(data.transcript);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="input-panel">
          <h1>YouTube Transcript</h1>
          <form className="url-form" onSubmit={fetchTranscript}>
            <label htmlFor="youtube-url">YouTube URL</label>
            <div className="input-row">
              <input
                id="youtube-url"
                type="url"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                required
              />
              <button type="submit" disabled={loading}>
                {loading ? "Fetching..." : "Fetch transcript"}
              </button>
            </div>
          </form>
          {error ? <p className="error">{error}</p> : null}
          {videoId ? <p className="video-id">Video ID: {videoId}</p> : null}
        </div>

        <div className="transcript-panel">
          <div className="panel-header">
            <h2>Raw Transcript</h2>
            <span>{transcript.length} entries</span>
          </div>

          {transcript.length ? (
            <ol className="transcript-list">
              {transcript.map((entry, index) => (
                <li key={`${entry.start}-${index}`} className="transcript-row">
                  <time>[{entry.timestamp}]</time>
                  <p>{entry.text}</p>
                </li>
              ))}
            </ol>
          ) : (
            <div className="empty-state">
              Paste a YouTube URL with captions to display the raw transcript.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
