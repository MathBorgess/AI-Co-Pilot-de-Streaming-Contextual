'use strict';

require('dotenv').config();
const express = require('express');
const http = require('http');
const { StreamEmitter } = require('./streamer');
const { WsServer } = require('./wsServer');

const PORT = process.env.PORT || 3001;
const AI_URL = process.env.AI_URL || 'http://localhost:8000';
const STREAM_INTERVAL = parseInt(process.env.STREAM_INTERVAL || '2000', 10);

const app = express();
app.use(express.json());

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.post('/start-stream', (req, res) => {
  if (streamer.isRunning()) {
    return res.json({ status: 'already_running' });
  }
  streamer.reset();
  streamer.start();
  res.json({ status: 'started' });
});

app.post('/stop-stream', (req, res) => {
  streamer.stop();
  res.json({ status: 'stopped' });
});

const server = http.createServer(app);
const wsServer = new WsServer({
  port: PORT,
  aiUrl: AI_URL,
  audioBufferMs: parseInt(process.env.AUDIO_BUFFER_MS || '1200', 10),
  onLiveModeChange: (isLive) => {
    if (isLive) {
      streamer.stop();
    }
  },
  onSimulatedStart: () => {
    if (!streamer.isRunning()) {
      streamer.reset();
      streamer.start();
    }
  },
  onSimulatedStop: () => {
    streamer.stop();
  },
});
wsServer.start(server);

const streamer = new StreamEmitter({
  intervalMs: STREAM_INTERVAL,
  onChunk: async (chunk, index, total) => {
    console.log(`[Stream] Chunk ${index}/${total}: ${chunk.substring(0, 50)}...`);
    
    wsServer.broadcast({
      type: 'chunk',
      chunk,
      chunkIndex: index,
      totalChunks: total,
    });

    const result = await wsServer.processChunk(chunk, index, total);
    if (result) {
      wsServer.broadcast({
        type: 'ai_update',
        ...result,
      });
    }
  },
  onComplete: () => {
    console.log('[Stream] Stream completed!');
    wsServer.broadcast({ type: 'stream_complete' });
  },
});

server.listen(PORT, () => {
  console.log(`[Server] HTTP + WS server running on port ${PORT}`);
  console.log(`[Server] AI URL: ${AI_URL}`);
});

module.exports = { app, server };
