'use strict';

const DEMO_TEXT = `We are here to make a final decision on the AI copilot launch strategy before the end of this meeting.
The deadline is end of next quarter and the engineering team says we absolutely cannot slip any further.
The team is split: half want to ship the current scope now, while others are deeply concerned about technical debt.
Our current architecture may not scale beyond fifty thousand concurrent users without a significant refactor.
The CTO is proposing we buy a third-party AI service instead of building the feature in-house.
Building in-house gives us full control and better margins, but will delay the launch by at least six weeks.
We need to decide today whether to build, buy, or delay the launch entirely — no more deferrals.
Legal has flagged serious concerns about data privacy compliance with the third-party vendor we evaluated.
Our main competitor launched a similar feature last week and is already gaining traction with enterprise clients.
If we delay any further, we risk losing three key enterprise accounts that are actively evaluating our platform now.
The engineering lead confirmed that the accumulated technical debt is a critical blocker for the six-month roadmap.
The recommendation is to ship a limited version this quarter and iterate toward the full in-house solution next cycle.`;

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
