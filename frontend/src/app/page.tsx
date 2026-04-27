'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import './globals.css';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';

interface AIUpdate {
  summary?: string;
  questions?: string[];
  insights?: string[];
  chunkIndex?: number;
  totalChunks?: number;
  processingTimeMs?: number;
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'streaming';

export default function Home() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [summary, setSummary] = useState('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [currentChunk, setCurrentChunk] = useState('');
  const [chunkInfo, setChunkInfo] = useState({ current: 0, total: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamComplete, setStreamComplete] = useState(false);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setStatus('connected');
      console.log('[WS] Connected');
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };

    socket.onclose = () => {
      setStatus('disconnected');
      console.log('[WS] Disconnected, reconnecting in 3s...');
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    socket.onerror = (err) => {
      console.error('[WS] Error:', err);
      socket.close();
    };
  }, []);

  const handleMessage = (msg: Record<string, unknown>) => {
    switch (msg.type) {
      case 'connected':
        setStatus('connected');
        break;

      case 'chunk':
        setStatus('streaming');
        setCurrentChunk(String(msg.chunk || ''));
        setChunkInfo({
          current: Number(msg.chunkIndex || 0),
          total: Number(msg.totalChunks || 0),
        });
        setIsProcessing(true);
        setStreamComplete(false);
        break;

      case 'ai_update': {
        const update = msg as AIUpdate;
        setIsProcessing(false);
        if (update.processingTimeMs !== undefined) {
          setProcessingTime(update.processingTimeMs);
        }
        if (update.summary) setSummary(update.summary);
        if (update.questions) setQuestions(update.questions);
        if (update.insights) setInsights(update.insights);
        break;
      }

      case 'stream_complete':
        setStatus('connected');
        setStreamComplete(true);
        setIsProcessing(false);
        setCurrentChunk('');
        break;

      default:
        break;
    }
  };

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const statusLabel = {
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
    streaming: 'Streaming',
  }[status];

  return (
    <div className="container">
      <div className="header">
        <h1>🤖 AI Co-Pilot Streaming Contextual</h1>
        <p>Real-time AI analysis with RAG + Multi-Agent Pipeline</p>
      </div>

      <div className="status-bar">
        <div className={`status-dot ${status}`} />
        <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{statusLabel}</span>

        {currentChunk && (
          <div className="current-chunk">
            &ldquo;{currentChunk.substring(0, 80)}{currentChunk.length > 80 ? '...' : ''}&rdquo;
          </div>
        )}

        {chunkInfo.total > 0 && (
          <div className="chunk-counter">
            Chunk {chunkInfo.current}/{chunkInfo.total}
          </div>
        )}

        {processingTime !== null && (
          <div className="chunk-counter" style={{ color: '#667eea' }}>
            ⚡ {processingTime}ms
          </div>
        )}
      </div>

      {streamComplete && (
        <div className="stream-complete">
          ✅ Stream complete! All chunks processed.
        </div>
      )}

      <div className="panels">
        {/* Summary Panel */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-icon">📝</span>
            <span className="panel-title">Cumulative Summary</span>
          </div>
          <div className="panel-content">
            {summary ? (
              <div className="summary-text">{summary}</div>
            ) : (
              <div className="empty-state">
                Waiting for content to summarize...
              </div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" />
                <span>Updating summary...</span>
              </div>
            )}
          </div>
        </div>

        {/* Questions Panel */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-icon">❓</span>
            <span className="panel-title">Suggested Questions</span>
          </div>
          <div className="panel-content">
            {questions.length > 0 ? (
              questions.map((q, i) => (
                <div key={i} className="question-item">
                  {q.replace(/^\?/, '').trim()}
                </div>
              ))
            ) : (
              <div className="empty-state">
                Questions will appear as content is processed...
              </div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" />
                <span>Generating questions...</span>
              </div>
            )}
          </div>
        </div>

        {/* Insights Panel */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-icon">💡</span>
            <span className="panel-title">Contextual Insights</span>
          </div>
          <div className="panel-content">
            {insights.length > 0 ? (
              insights.map((insight, i) => (
                <div key={i} className="insight-item">
                  {insight.replace(/^→/, '').trim()}
                </div>
              ))
            ) : (
              <div className="empty-state">
                Insights will appear as patterns are detected...
              </div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" />
                <span>Analyzing patterns...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
