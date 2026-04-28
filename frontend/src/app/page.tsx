'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import './globals.css';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';

interface AlertItem {
  emoji: string;
  label: string;
  detail: string;
}

interface AIUpdate {
  summary?: string;
  questions?: string[];
  insights?: string[];
  alerts?: AlertItem[];
  directions?: string[];
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
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [directions, setDirections] = useState<string[]>([]);
  const [currentChunk, setCurrentChunk] = useState('');
  const [chunkInfo, setChunkInfo] = useState({ current: 0, total: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamComplete, setStreamComplete] = useState(false);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [latestAlertKey, setLatestAlertKey] = useState(0);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setStatus('connected');
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
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    socket.onerror = () => {
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
        if (update.processingTimeMs !== undefined) setProcessingTime(update.processingTimeMs);
        if (update.summary) setSummary(update.summary);
        if (update.questions) setQuestions(update.questions);
        if (update.insights) setInsights(update.insights);
        if (update.directions) setDirections(update.directions);
        if (update.alerts) {
          setAlerts(update.alerts);
          if (update.alerts.length > 0) {
            // Bump key to re-trigger the flash animation on the latest alert
            setLatestAlertKey((k) => k + 1);
          }
        }
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
    connected: 'Connected — Awaiting Stream',
    disconnected: 'Disconnected',
    streaming: '🔴 LIVE',
  }[status];

  const latestAlert = alerts.length > 0 ? alerts[alerts.length - 1] : null;

  return (
    <div className="container">
      <div className="header">
        <h1>🤖 AI Co-Pilot — Live Meeting Intelligence</h1>
        <p>Real-time decisions · risks · insights · next steps</p>
      </div>

      {/* Status bar */}
      <div className="status-bar">
        <div className={`status-dot ${status}`} />
        <span className="status-label">{statusLabel}</span>

        {currentChunk && (
          <div className="current-chunk">
            &ldquo;{currentChunk.substring(0, 90)}{currentChunk.length > 90 ? '…' : ''}&rdquo;
          </div>
        )}

        {chunkInfo.total > 0 && (
          <div className="chunk-counter">
            {chunkInfo.current} / {chunkInfo.total}
          </div>
        )}

        {isProcessing && (
          <div className="thinking-badge">
            <div className="spinner" /> AI thinking…
          </div>
        )}

        {processingTime !== null && !isProcessing && (
          <div className="chunk-counter" style={{ color: '#667eea' }}>
            ⚡ {processingTime}ms
          </div>
        )}
      </div>

      {/* Live Alerts feed — full width, high impact */}
      {latestAlert && (
        <div className="alerts-section" key={latestAlertKey}>
          <div className="alerts-header">
            <span>🚨 LIVE ALERTS</span>
            <span className="alert-count">{alerts.length} event{alerts.length !== 1 ? 's' : ''} detected</span>
          </div>
          <div className="alerts-list">
            {alerts.slice().reverse().map((alert, i) => (
              <div
                key={`${alert.label}-${i}`}
                className={`alert-card ${i === 0 ? 'alert-card--new' : 'alert-card--old'}`}
              >
                <span className="alert-emoji">{alert.emoji}</span>
                <div className="alert-body">
                  <div className="alert-label">{alert.label}</div>
                  <div className="alert-detail">{alert.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {streamComplete && (
        <div className="stream-complete">
          ✅ Meeting stream ended — {alerts.length} key moment{alerts.length !== 1 ? 's' : ''} captured.
        </div>
      )}

      {/* 2×2 panel grid */}
      <div className="panels">
        {/* Summary */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-icon">📝</span>
            <span className="panel-title">Cumulative Summary</span>
          </div>
          <div className="panel-content">
            {summary ? (
              <div className="summary-text">{summary}</div>
            ) : (
              <div className="empty-state">Waiting for content…</div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" /><span>Updating summary…</span>
              </div>
            )}
          </div>
        </div>

        {/* Questions */}
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
              <div className="empty-state">Questions will appear as content is processed…</div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" /><span>Generating questions…</span>
              </div>
            )}
          </div>
        </div>

        {/* Insights */}
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
              <div className="empty-state">Insights will appear as patterns are detected…</div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" /><span>Analysing patterns…</span>
              </div>
            )}
          </div>
        </div>

        {/* Directions — new panel */}
        <div className="panel panel--directions">
          <div className="panel-header">
            <span className="panel-icon">🧭</span>
            <span className="panel-title">Recommended Actions</span>
          </div>
          <div className="panel-content">
            {directions.length > 0 ? (
              directions.map((d, i) => (
                <div key={i} className="direction-item">
                  <span className="direction-arrow">→</span>
                  <span>{d.replace(/^→/, '').trim()}</span>
                </div>
              ))
            ) : (
              <div className="empty-state">Actions will appear as context builds…</div>
            )}
            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner" /><span>Recommending next steps…</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
