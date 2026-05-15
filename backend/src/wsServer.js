'use strict';

const WebSocket = require('ws');
const axios = require('axios');

class WsServer {
  constructor(options = {}) {
    this.port = options.port || 3001;
    this.aiUrl = options.aiUrl || 'http://localhost:8000';
    this.wss = null;
    this.clients = new Set();
    this.liveMode = false;
    this.liveChunkIndex = 0;
    this.audioBufferMs = options.audioBufferMs || 1200;
    this.audioBuffers = new Map();
    this.audioTimers = new Map();
    this.onLiveModeChange = options.onLiveModeChange || null;
    this.onSimulatedStart = options.onSimulatedStart || null;
    this.onSimulatedStop = options.onSimulatedStop || null;
  }

  start(server) {
    this.wss = new WebSocket.Server(server ? { server } : { port: this.port });

    this.wss.on('connection', (ws) => {
      this.clients.add(ws);
      console.log(`[WS] Client connected. Total: ${this.clients.size}`);

      ws.send(JSON.stringify({ type: 'connected', message: 'AI Co-Pilot connected!' }));

      ws.on('message', async (data) => {
        await this.handleClientMessage(ws, data);
      });

      ws.on('close', () => {
        this.clearAudioState(ws);
        this.clients.delete(ws);
        console.log(`[WS] Client disconnected. Total: ${this.clients.size}`);
      });

      ws.on('error', (err) => {
        console.error('[WS] Client error:', err.message);
        this.clearAudioState(ws);
        this.clients.delete(ws);
      });
    });

    console.log(`[WS] Server started on port ${this.port}`);
    return this.wss;
  }

  setLiveMode(isLive) {
    this.liveMode = isLive;
    this.liveChunkIndex = 0;
    if (this.onLiveModeChange) {
      this.onLiveModeChange(isLive);
    }
  }

  clearAudioState(ws) {
    const timer = this.audioTimers.get(ws);
    if (timer) clearTimeout(timer);
    this.audioTimers.delete(ws);
    this.audioBuffers.delete(ws);
  }

  async handleClientMessage(ws, data) {
    let msg;
    try {
      const text = Buffer.isBuffer(data) ? data.toString('utf8') : String(data);
      msg = JSON.parse(text);
    } catch (err) {
      console.warn('[WS] Ignoring non-JSON message');
      return;
    }

    switch (msg.type) {
      case 'start_live':
        this.setLiveMode(true);
        if (this.onSimulatedStop) this.onSimulatedStop();
        this.broadcast({ type: 'system_status', liveMode: true });
        break;
      case 'stop_live':
        this.setLiveMode(false);
        this.broadcast({ type: 'system_status', liveMode: false });
        break;
      case 'start_simulated':
        this.liveMode = false;
        if (this.onSimulatedStart) this.onSimulatedStart();
        this.broadcast({ type: 'system_status', liveMode: false });
        break;
      case 'stop_simulated':
        if (this.onSimulatedStop) this.onSimulatedStop();
        break;
      case 'text_chunk':
        await this.handleTextChunk(msg.text || '', msg.isFinal !== false);
        break;
      case 'audio_chunk':
        await this.handleAudioChunk(ws, msg);
        break;
      default:
        break;
    }
  }

  async handleTextChunk(text, isFinal) {
    if (!text || !text.trim()) return;
    if (!isFinal) {
      this.broadcast({ type: 'transcript_update', text, isFinal: false });
      return;
    }

    this.liveChunkIndex += 1;
    this.broadcast({
      type: 'chunk',
      chunk: text,
      chunkIndex: this.liveChunkIndex,
      totalChunks: 0,
      source: 'live',
    });

    const result = await this.processChunk(text, this.liveChunkIndex, 0);
    if (result) {
      this.broadcast({ type: 'ai_update', source: 'live', ...result });
    }
  }

  async handleAudioChunk(ws, msg) {
    if (!msg.payload) return;
    const buffer = Buffer.from(msg.payload, 'base64');
    if (!this.audioBuffers.has(ws)) {
      this.audioBuffers.set(ws, { chunks: [], mimeType: msg.mimeType || 'audio/webm' });
    }

    const state = this.audioBuffers.get(ws);
    state.chunks.push(buffer);
    state.mimeType = msg.mimeType || state.mimeType;

    if (!this.audioTimers.has(ws)) {
      const timer = setTimeout(async () => {
        this.audioTimers.delete(ws);
        await this.flushAudio(ws);
      }, this.audioBufferMs);
      this.audioTimers.set(ws, timer);
    }
  }

  async flushAudio(ws) {
    const state = this.audioBuffers.get(ws);
    if (!state || state.chunks.length === 0) return;
    const audioBuffer = Buffer.concat(state.chunks);
    state.chunks = [];

    const result = await this.transcribeAudio(audioBuffer, state.mimeType);
    if (!result || !result.text) return;

    this.broadcast({
      type: 'transcript_update',
      text: result.text,
      isFinal: result.isFinal !== false,
    });

    if (result.isFinal !== false) {
      await this.handleTextChunk(result.text, true);
    }
  }

  async transcribeAudio(audioBuffer, mimeType) {
    try {
      const response = await axios.post(`${this.aiUrl}/transcribe`, {
        audioBase64: audioBuffer.toString('base64'),
        mimeType,
      }, { timeout: 30000 });
      return response.data;
    } catch (err) {
      console.error('[AI] Error transcribing audio:', err.message);
      return null;
    }
  }

  broadcast(data) {
    const message = JSON.stringify(data);
    this.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  async processChunk(chunk, chunkIndex, totalChunks) {
    try {
      const response = await axios.post(`${this.aiUrl}/process`, {
        chunk,
        chunkIndex,
        totalChunks,
      }, { timeout: 30000 });

      return response.data;
    } catch (err) {
      console.error('[AI] Error processing chunk:', err.message);
      return null;
    }
  }

  getClientCount() {
    return this.clients.size;
  }

  close() {
    if (this.wss) {
      this.wss.close();
    }
  }
}

module.exports = { WsServer };
