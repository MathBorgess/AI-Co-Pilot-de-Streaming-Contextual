'use strict';

const WebSocket = require('ws');
const { WsServer } = require('../src/wsServer');

jest.mock('axios');
const axios = require('axios');

describe('WsServer', () => {
  let wsServer;
  let port;

  beforeEach(() => {
    port = 3099;
    wsServer = new WsServer({ port });
    wsServer.start();
  });

  afterEach((done) => {
    wsServer.close();
    setTimeout(done, 100);
  });

  test('should start and accept connections', (done) => {
    const client = new WebSocket(`ws://localhost:${port}`);
    client.on('open', () => {
      expect(wsServer.getClientCount()).toBe(1);
      client.close();
      done();
    });
  });

  test('should broadcast to all connected clients', (done) => {
    const client1 = new WebSocket(`ws://localhost:${port}`);
    const messages = [];

    client1.on('open', () => {
      // Skip the connected message
      client1.on('message', (data) => {
        const msg = JSON.parse(data);
        if (msg.type === 'test') {
          messages.push(msg);
          expect(messages[0].content).toBe('hello');
          client1.close();
          done();
        }
      });

      setTimeout(() => {
        wsServer.broadcast({ type: 'test', content: 'hello' });
      }, 50);
    });
  });

  test('should call AI endpoint on processChunk', async () => {
    axios.post.mockResolvedValue({
      data: { summary: 'test', questions: [], insights: [] },
    });

    const result = await wsServer.processChunk('test chunk', 1, 5);
    expect(result).toEqual({ summary: 'test', questions: [], insights: [] });
    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/process'),
      expect.objectContaining({ chunk: 'test chunk' }),
      expect.any(Object)
    );
  });

  test('should return null on AI error', async () => {
    axios.post.mockRejectedValue(new Error('Network error'));
    const result = await wsServer.processChunk('test chunk', 1, 5);
    expect(result).toBeNull();
  });

  test('should track client count correctly', (done) => {
    expect(wsServer.getClientCount()).toBe(0);
    const client = new WebSocket(`ws://localhost:${port}`);
    client.on('open', () => {
      expect(wsServer.getClientCount()).toBe(1);
      client.close();
      setTimeout(() => {
        expect(wsServer.getClientCount()).toBe(0);
        done();
      }, 100);
    });
  });
});
