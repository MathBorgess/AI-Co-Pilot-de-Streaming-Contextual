'use strict';

const DEMO_TEXT = `Hoje precisamos de uma decisao final sobre o copiloto de streaming para o mercado enterprise.
O prazo do trimestre fecha em 6 semanas e nao podemos atrasar a janela de go/no-go.
A equipe esta dividida: metade quer shipar o MVP agora, a outra metade teme a divida tecnica.
A arquitetura atual nao escala acima de 50k usuarios concorrentes sem um refactor critico.
O CTO quer comprar um provedor externo de IA para ganhar time-to-market.
Build in-house aumenta margem, mas empurra o lancamento em pelo menos 6 semanas.
Precisamos decidir hoje: build, buy ou adiar - sem mais deferrals.
Legal flagou risco serio de compliance e privacidade com o fornecedor avaliado.
O concorrente X lancou a feature semana passada e ja ganhou tracao em contas enterprise.
Isso redefine nossa estrategia de posicionamento e o escopo do MVP.
Se atrasarmos, perdemos 3 contas em fase final de negociacao e o ROI do trimestre cai.
O budget atual so cobre o MVP; qualquer escopo extra exige aprovacao do board.
O insight principal: o diferencial real e a integracao ao fluxo ao vivo, nao o modelo em si.
Recomendacao: shipar um MVP restrito agora e iniciar o plano de migracao para in-house no proximo ciclo.`;

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
