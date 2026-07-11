import React, { useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE_URL = "http://localhost:8000/api";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [videoId, setVideoId] = useState("");
  const [transcript, setTranscript] = useState([]);
  const [chunks, setChunks] = useState([]);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [conversationId, setConversationId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const playerRef = useRef(null);

  async function fetchTranscript(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setVideoId("");
    setTranscript([]);
    setChunks([]);
    setSearchResults([]);
    setMessages([]);
    setConversationId("");

    try {
      const response = await fetch(`${API_BASE_URL}/transcript`, {
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

  async function indexVideo(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setVideoId("");
    setTranscript([]);
    setChunks([]);
    setSearchResults([]);
    setMessages([]);
    setConversationId("");

    try {
      const response = await fetch(`${API_BASE_URL}/index`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not index video.");
      }

      setVideoId(data.video_id);
      setChunks(data.chunks);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function askQuestion(event) {
    event.preventDefault();
    const question = chatInput.trim();
    if (!question || !videoId) {
      return;
    }

    setChatInput("");
    setChatLoading(true);
    setError("");
    setMessages((current) => [
      ...current,
      { role: "user", content: question },
    ]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          video_id: videoId,
          message: question,
          conversation_id: conversationId || null,
          limit: 6,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not answer question.");
      }

      setConversationId(data.conversation_id);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          rewrittenQuery: data.rewritten_query,
        },
      ]);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setChatLoading(false);
    }
  }

  function seekTo(seconds) {
    if (!playerRef.current) {
      return;
    }

    playerRef.current.contentWindow.postMessage(
      JSON.stringify({
        event: "command",
        func: "seekTo",
        args: [seconds, true],
      }),
      "*",
    );
    playerRef.current.contentWindow.postMessage(
      JSON.stringify({
        event: "command",
        func: "playVideo",
        args: [],
      }),
      "*",
    );
  }

  const playerUrl = videoId
    ? `https://www.youtube.com/embed/${videoId}?enablejsapi=1`
    : "";

  async function searchChunks(event) {
    event.preventDefault();
    setSearching(true);
    setError("");
    setSearchResults([]);

    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          video_id: videoId,
          query,
          limit: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not search chunks.");
      }

      setSearchResults(data.results);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setSearching(false);
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
              <button type="button" disabled={loading} onClick={indexVideo}>
                {loading ? "Indexing..." : "Index chunks"}
              </button>
            </div>
          </form>
          {error ? <p className="error">{error}</p> : null}
          {videoId ? <p className="video-id">Video ID: {videoId}</p> : null}
          {chunks.length ? (
            <form className="search-form" onSubmit={searchChunks}>
              <label htmlFor="search-query">Search indexed chunks</label>
              <input
                id="search-query"
                type="search"
                placeholder="Ask about a topic in this video"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                required
              />
              <button type="submit" disabled={searching || !videoId}>
                {searching ? "Searching..." : "Search"}
              </button>
            </form>
          ) : null}

          {videoId ? (
            <div className="player-shell">
              <iframe
                ref={playerRef}
                title="YouTube video player"
                src={playerUrl}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          ) : null}

          {chunks.length ? (
            <form className="chat-form" onSubmit={askQuestion}>
              <label htmlFor="chat-question">Ask with citations</label>
              <textarea
                id="chat-question"
                placeholder="Ask a question about the indexed video"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                required
              />
              <button type="submit" disabled={chatLoading || !videoId}>
                {chatLoading ? "Answering..." : "Ask"}
              </button>
            </form>
          ) : null}
        </div>

        <div className="transcript-panel">
          <div className="panel-header">
            <h2>{chunks.length ? "Indexed Chunks" : "Raw Transcript"}</h2>
            <span>
              {chunks.length
                ? `${chunks.length} chunks`
                : `${transcript.length} entries`}
            </span>
          </div>

          {searchResults.length ? (
            <ol className="transcript-list">
              {searchResults.map((result) => (
                <li key={result.id} className="chunk-row">
                  <div className="chunk-meta">
                    <time>
                      [{result.start_timestamp}-{result.end_timestamp}]
                    </time>
                    <span>Distance {result.distance?.toFixed(4)}</span>
                  </div>
                  <p>{result.text}</p>
                </li>
              ))}
            </ol>
          ) : chunks.length ? (
            <ol className="transcript-list">
              {chunks.map((chunk) => (
                <li key={chunk.id} className="chunk-row">
                  <div className="chunk-meta">
                    <time>
                      [{chunk.start_timestamp}-{chunk.end_timestamp}]
                    </time>
                    <span>Chunk {chunk.chunk_index + 1}</span>
                  </div>
                  <p>{chunk.text}</p>
                </li>
              ))}
            </ol>
          ) : transcript.length ? (
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
              Paste a YouTube URL with captions to fetch a transcript or index chunks.
            </div>
          )}
        </div>

        <div className="chat-panel">
          <div className="panel-header">
            <h2>Q&A</h2>
            <span>{messages.length} messages</span>
          </div>
          {messages.length ? (
            <ol className="message-list">
              {messages.map((message, index) => (
                <li key={`${message.role}-${index}`} className={`message ${message.role}`}>
                  <p>{message.content}</p>
                  {message.rewrittenQuery ? (
                    <small>Search: {message.rewrittenQuery}</small>
                  ) : null}
                  {message.citations?.length ? (
                    <div className="citation-list">
                      {message.citations.map((citation) => (
                        <button
                          key={citation.id}
                          type="button"
                          className="citation-button"
                          onClick={() => seekTo(citation.start)}
                        >
                          {citation.start_timestamp}-{citation.end_timestamp}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </li>
              ))}
            </ol>
          ) : (
            <div className="empty-state">
              Index a video, then ask questions to get cited answers.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
