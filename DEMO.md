# AI Streaming Copilot - Demo & Learnings (v2)

> "Isso nao e um chatbot. Ele esta entendendo o que acontece em tempo real."

---

## 1. Introducao (1 min)

### Problema
Ferramentas de AI tradicionais so respondem quando voce pergunta. Mas a vida real acontece em **fluxo continuo**: reunioes criticas, incidentes ao vivo, decisao de produto, conflitos de prioridade.

Quando a conversa termina, o contexto ja passou.

### Tendencia
Tres forcas convergem e tornam isso possivel agora:
- **Streaming AI** - modelos conseguem processar incrementalmente
- **Multi-agent systems** - agentes especializados superam um monolito
- **RAG** - contexto fica mais forte a cada novo chunk

### Tese da demo
Um copiloto que **ouve sozinho**, detecta decisoes e riscos, e sugere proximos passos antes da reuniao acabar.

---

## 2. O que foi construido (2 min)

### Pipeline (alto nivel)

```
Stream (texto) -> Node.js (WS) -> FastAPI (AI)
  -> RAG (Chroma + recency + focus terms)
  -> Agents: Summary + Questions + Insights + Alert + Action
  -> WebSocket -> UI (tempo real)
```

### Diferencial vs chatbot
- **Passivo**: chatbot responde quando perguntado
- **Ativo**: este sistema reage a eventos e sinaliza momentos-chave

### Antes vs Depois (passivo -> ativo)

| Antes (passivo) | Depois (ativo) |
| --- | --- |
| Usuario pergunta | Sistema observa e reage |
| Resposta isolada | Contexto acumulado (RAG) |
| Sem alertas | Key Moments em tempo real |
| Sem recomendacoes | Action Agent sugere proximos passos |

---

## 3. Demo ao vivo (4 min)

### Narrativa do cenario
"Reuniao de estrategia: build vs buy, prazo apertado, risco juridico, concorrente lancou, time dividido."  
O sistema precisa detectar esses momentos em tempo real.

### Como rodar

```bash
npm run dev
```

Primeira vez? Siga o guia em SETUP_FREE.md.

Abra http://localhost:3000

### O que destacar durante a demo
- Clique em "Start Live Mode" e fale: "Agora isso nao e mais simulado... ele esta ouvindo em tempo real."
- **Key Moments**: alertas disparam quando aparece "decisao", "prazo", "risco", "concorrente"
- **Action Agent**: sugere proximos passos antes da conversa terminar
- **Focus terms**: o sistema mostra os termos que estao dominando o contexto
- **Latencia**: resposta em menos de 3s por chunk

### Momento WOW (obrigatorio)
Quando surge "Legal flagou risco de compliance", o alerta aparece instantaneamente.  
Voce nao pediu nada. Ele entendeu e reagiu.

---

## 4. Decisoes tecnicas (1-2 min)

### Alert Agent (pattern matching)
- Instantaneo, sem latencia de LLM
- Mais confiavel para demos ao vivo

### Action Agent (templates + contexto)
- Em mock mode, usa templates orientados por palavras-chave e alertas
- Em live mode, gera recomendacoes com LLM

### RAG com recency + focus terms
- Recency garante o chunk atual no contexto
- Focus terms reforcam os topicos que estao se repetindo

---

## 5. Aprendizados (1-2 min)

### O que funcionou
- Alertas mudam a percepcao: nao parece chatbot, parece sistema vivo
- Action Agent cria sensacao de proatividade
- UI em tempo real da clareza em menos de 30s

### O que nao funcionou tao bem
- Mock mode limita diversidade de respostas
- Alertas ainda nao entendem negacao ("sem risco" dispara "risco")

### Limitacoes
- Stream ainda e roteirizado
- Nao ha timeline historica completa

### Proximos passos
- Severidade nos alertas (low/med/high)
- Timeline view de momentos-chave
- Streaming de tokens para respostas ainda mais vivas

---

## Checklist rapido para apresentacao

- Abra a UI e fale: "Nao e chatbot. Ele reage a eventos"
- Mostre o painel de Key Moments piscando
- Mostre o Action Agent sugerindo decisoes
- Se precisar, use "Switch to simulated mode" para voltar ao fluxo roteirizado
- Feche com: "Isso muda como voce pensa sobre streaming e AI"
