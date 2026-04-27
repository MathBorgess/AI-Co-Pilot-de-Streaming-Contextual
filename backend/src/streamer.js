'use strict';

const DEMO_TEXT = `Artificial intelligence is transforming how we interact with technology.
Machine learning models can now understand context and generate meaningful responses.
Large language models have revolutionized natural language processing tasks.
Streaming systems allow for real-time processing of continuous data flows.
Event-driven architectures enable scalable and responsive applications.
Retrieval-augmented generation combines search with language model capabilities.
Multi-agent systems can coordinate to solve complex problems collaboratively.
Vector databases store semantic representations of text for efficient search.
WebSockets enable bidirectional real-time communication between clients and servers.
The future of AI involves increasingly autonomous and collaborative systems.
Contextual understanding is key to building useful AI assistants.
Incremental processing allows systems to respond before all data is available.`;

class StreamEmitter {
  constructor(options = {}) {
    this.text = options.text || DEMO_TEXT;
    this.chunkSize = options.chunkSize || 1;
    this.intervalMs = options.intervalMs || 2000;
    this.sentences = this.text.split('\n').filter(s => s.trim().length > 0);
    this.currentIndex = 0;
    this.timer = null;
    this.onChunk = options.onChunk || (() => {});
    this.onComplete = options.onComplete || (() => {});
  }

  start() {
    this.currentIndex = 0;
    this._emitNext();
  }

  _emitNext() {
    if (this.currentIndex >= this.sentences.length) {
      this.timer = null;
      this.onComplete();
      return;
    }

    const chunk = this.sentences[this.currentIndex];
    this.currentIndex++;

    // Schedule the next chunk before calling onChunk so stop() can cancel it
    this.timer = setTimeout(() => this._emitNext(), this.intervalMs);

    this.onChunk(chunk, this.currentIndex, this.sentences.length);
  }

  stop() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  reset() {
    this.stop();
    this.currentIndex = 0;
  }

  isRunning() {
    return this.timer !== null;
  }
}

module.exports = { StreamEmitter, DEMO_TEXT };
