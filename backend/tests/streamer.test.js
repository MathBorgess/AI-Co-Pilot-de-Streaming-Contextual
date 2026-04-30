'use strict';

const { StreamEmitter, DEMO_TEXT } = require('../src/streamer');

describe('StreamEmitter', () => {
  test('should initialize with default values', () => {
    const emitter = new StreamEmitter();
    expect(emitter.sentences.length).toBeGreaterThan(0);
    expect(emitter.currentIndex).toBe(0);
    expect(emitter.isRunning()).toBe(false);
  });

  test('should split text into sentences', () => {
    const emitter = new StreamEmitter({ text: 'Line one.\nLine two.\nLine three.' });
    expect(emitter.sentences).toEqual(['Line one.', 'Line two.', 'Line three.']);
  });

  test('should call onChunk with correct arguments', (done) => {
    const chunks = [];
    const emitter = new StreamEmitter({
      text: 'Hello world.\nSecond line.',
      intervalMs: 10,
      onChunk: (chunk, index, total) => {
        chunks.push({ chunk, index, total });
        if (chunks.length === 1) {
          emitter.stop();
          expect(chunks[0].chunk).toBe('Hello world.');
          expect(chunks[0].index).toBe(1);
          expect(chunks[0].total).toBe(2);
          done();
        }
      },
    });
    emitter.start();
  });

  test('should call onComplete when all chunks are emitted', (done) => {
    const emitter = new StreamEmitter({
      text: 'Only one line.',
      intervalMs: 10,
      onComplete: () => {
        done();
      },
    });
    emitter.start();
  });

  test('should reset correctly', () => {
    const emitter = new StreamEmitter({ text: 'Line one.\nLine two.' });
    emitter.currentIndex = 5;
    emitter.reset();
    expect(emitter.currentIndex).toBe(0);
    expect(emitter.isRunning()).toBe(false);
  });

  test('DEMO_TEXT should be a non-empty string', () => {
    expect(typeof DEMO_TEXT).toBe('string');
    expect(DEMO_TEXT.length).toBeGreaterThan(0);
  });

  test('should stop emitting after stop() is called', (done) => {
    let count = 0;
    const emitter = new StreamEmitter({
      text: 'Line 1.\nLine 2.\nLine 3.',
      intervalMs: 10,
      onChunk: () => {
        count++;
        if (count === 1) {
          emitter.stop();
          setTimeout(() => {
            expect(count).toBe(1);
            done();
          }, 50);
        }
      },
    });
    emitter.start();
  });
});
