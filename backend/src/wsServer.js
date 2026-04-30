'use strict';

const WebSocket = require('ws');
const axios = require('axios');

class WsServer {
  constructor(options = {}) {
    this.port = options.port || 3001;
    this.aiUrl = options.aiUrl || 'http://localhost:8000';
    this.wss = null;
    this.clients = new Set();
  }

  start(server) {
    this.wss = new WebSocket.Server(server ? { server } : { port: this.port });

    this.wss.on('connection', (ws) => {
      this.clients.add(ws);
      console.log(`[WS] Client connected. Total: ${this.clients.size}`);

      ws.send(JSON.stringify({ type: 'connected', message: 'AI Co-Pilot connected!' }));

      ws.on('close', () => {
        this.clients.delete(ws);
        console.log(`[WS] Client disconnected. Total: ${this.clients.size}`);
      });

      ws.on('error', (err) => {
        console.error('[WS] Client error:', err.message);
        this.clients.delete(ws);
      });
    });

    console.log(`[WS] Server started on port ${this.port}`);
    return this.wss;
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
