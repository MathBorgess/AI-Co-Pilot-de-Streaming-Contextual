'use strict';

jest.mock('axios');
const axios = require('axios');
const WebSocket = require('ws');
const { StreamEmitter } = require('../src/streamer');
const { WsServer } = require('../src/wsServer');

describe('Integration: Stream → WS → AI', () => {
  let wsServer;
  const port = 3098;

  beforeEach(() => {
    wsServer = new WsServer({ port });
    wsServer.start();

    axios.post.mockImplementation(async (url, body) => {
      if (url.includes('/process')) {
        return {
          data: {
            summary: `Summary of: ${body.chunk}`,
            questions: [`What is ${body.chunk.split(' ')[0]}?`],
            insights: [`Insight about chunk ${body.chunkIndex}`],
          },
        };
      }
      return { data: {} };
    });
  });

  afterEach((done) => {
    wsServer.close();
    setTimeout(done, 200);
  });

  test('full pipeline: stream emitter sends chunks, WS broadcasts AI results', (done) => {
    const receivedMessages = [];
    const client = new WebSocket(`ws://localhost:${port}`);

    client.on('open', () => {
      const streamer = new StreamEmitter({
        text: 'First sentence.\nSecond sentence.',
        intervalMs: 50,
        onChunk: async (chunk, index, total) => {
          wsServer.broadcast({ type: 'chunk', chunk, chunkIndex: index, totalChunks: total });
          const result = await wsServer.processChunk(chunk, index, total);
          if (result) {
            wsServer.broadcast({ type: 'ai_update', ...result });
          }
        },
        onComplete: () => {
          wsServer.broadcast({ type: 'stream_complete' });
          
          setTimeout(() => {
            client.close();
            
            const aiUpdates = receivedMessages.filter(m => m.type === 'ai_update');
            const completeMsg = receivedMessages.find(m => m.type === 'stream_complete');

            expect(aiUpdates.length).toBe(2);
            expect(completeMsg).toBeDefined();
            expect(aiUpdates[0].summary).toContain('First sentence');
            done();
          }, 100);
        },
      });

      streamer.start();
    });

    client.on('message', (data) => {
      const msg = JSON.parse(data);
      receivedMessages.push(msg);
    });
  });

  test('should handle AI errors gracefully', (done) => {
    axios.post.mockRejectedValue(new Error('AI unavailable'));
    
    let chunkBroadcasted = false;
    const client = new WebSocket(`ws://localhost:${port}`);

    client.on('open', () => {
      const streamer = new StreamEmitter({
        text: 'Test chunk.',
        intervalMs: 50,
        onChunk: async (chunk, index, total) => {
          wsServer.broadcast({ type: 'chunk', chunk });
          const result = await wsServer.processChunk(chunk, index, total);
          expect(result).toBeNull();
          chunkBroadcasted = true;
        },
        onComplete: () => {
          setTimeout(() => {
            expect(chunkBroadcasted).toBe(true);
            client.close();
            done();
          }, 50);
        },
      });

      streamer.start();
    });
  });
});
