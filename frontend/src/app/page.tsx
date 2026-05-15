'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import './globals.css';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001';

const THINKING_MESSAGES = [
  'Analyzing the discussion...',
  'Detecting decisions...',
  'Evaluating risks...',
  'Updating meeting understanding...',
  'Refining the next recommendation...',
];

const LISTENING_MESSAGES = [
  'Listening to the conversation...',
  'Tracking what changed in the room...',
  'Following commitments and concerns...',
];

const ALERT_LABELS: Record<string, string> = {
  'Key Decision Detected': 'The AI thinks a decision is being made',
  'Risk Signal Identified': 'This might be a risk',
  'Time Pressure Detected': 'Timeline pressure just surfaced',
  'Team Conflict Detected': 'The team sounds split',
  'Competitive Signal': 'Competitive pressure detected',
  'Financial Implication': 'This could impact budget',
  'Critical Issue Flagged': 'This looks like a blocker',
  'Critical Concept': 'A critical concept just emerged',
  'Important Insight': 'The AI noticed a new insight',
};

const ALERT_IMPACTS: Record<string, string> = {
  'Key Decision Detected': 'Impact: this needs alignment and an owner.',
  'Risk Signal Identified': 'Impact: potential risk to delivery or compliance.',
  'Time Pressure Detected': 'Impact: timeline may force scope changes.',
  'Team Conflict Detected': 'Impact: misalignment can slow decisions.',
  'Competitive Signal': 'Impact: market pressure could shift priorities.',
  'Financial Implication': 'Impact: budget or ROI may be affected.',
  'Critical Issue Flagged': 'Impact: blocker could stall the roadmap.',
  'Critical Concept': 'Impact: strategic framing could reshape scope.',
  'Important Insight': 'Impact: insight can guide the next action.',
};

const ALERT_REASONS: Record<string, string> = {
  'Key Decision Detected': 'Because: commitment language and a decision cue.',
  'Risk Signal Identified': 'Because: risk/compliance terms were mentioned.',
  'Time Pressure Detected': 'Because: deadlines and urgency cues surfaced.',
  'Team Conflict Detected': 'Because: disagreement or split signals appeared.',
  'Competitive Signal': 'Because: competitor or market pressure was cited.',
  'Financial Implication': 'Because: budget or ROI was referenced.',
  'Critical Issue Flagged': 'Because: blocker or critical issue language was used.',
  'Critical Concept': 'Because: strategy or architecture framing emerged.',
  'Important Insight': 'Because: a new insight or pattern was stated.',
};

const ALERT_SEVERITY: Record<string, 'risk' | 'decision' | 'insight'> = {
  'Risk Signal Identified': 'risk',
  'Critical Issue Flagged': 'risk',
  'Time Pressure Detected': 'decision',
  'Key Decision Detected': 'decision',
  'Team Conflict Detected': 'decision',
  'Financial Implication': 'decision',
  'Competitive Signal': 'decision',
  'Critical Concept': 'insight',
  'Important Insight': 'insight',
};

const ALERT_UNDERSTANDING: Record<string, string> = {
  'Key Decision Detected': 'A decision point is active and needs clear ownership.',
  'Risk Signal Identified': 'Legal or compliance uncertainty may block approval.',
  'Time Pressure Detected': 'Timeline pressure is increasing and may force trade-offs.',
  'Team Conflict Detected': 'Alignment risk is growing across the team.',
  'Competitive Signal': 'External market pressure is influencing urgency.',
  'Financial Implication': 'Budget impact is becoming part of the decision.',
  'Critical Issue Flagged': 'A blocker could stall the current plan.',
  'Critical Concept': 'A strategic framing is reshaping priorities.',
  'Important Insight': 'A useful pattern emerged and should guide next steps.',
};

const KEYWORDS = [
  'decisao', 'decidir', 'decision', 'risk', 'risco', 'prazo', 'deadline',
  'urgent', 'urgente', 'compliance', 'legal', 'budget', 'custo',
  'concorrente', 'competitor', 'bloqueador', 'blocker',
];

const KEYWORD_SET = new Set(KEYWORDS.map((term) => term.toLowerCase()));
const KEYWORD_REGEX = new RegExp(`(${KEYWORDS.join('|')})`, 'gi');

const formatAlertLabel = (label: string) => ALERT_LABELS[label] || label;
const formatAlertImpact = (label: string) => ALERT_IMPACTS[label] || 'Impact: worth tracking.';
const formatAlertReason = (label: string) => ALERT_REASONS[label] || 'Because: the AI detected a signal.';
const getAlertSeverity = (label: string) => ALERT_SEVERITY[label] || 'insight';

const getSemanticModeLabel = (mode?: string) => {
  const normalized = (mode || '').toLowerCase();
  if (normalized === 'brainstorming') return 'Suggested Exploration';
  if (normalized === 'teaching') return 'Learning Focus';
  if (normalized === 'technical discussion') return 'Technical Focus';
  if (normalized === 'decision making') return 'Decision Focus';
  if (normalized === 'analysis') return 'Analytical Focus';
  if (normalized === 'debate') return 'Debate Focus';
  return 'CURRENT AI FOCUS';
};

const getSemanticAlertTitle = (label: string, conversation?: AIUpdate['conversation']) => {
  const mode = (conversation?.mode || '').toLowerCase();
  const domain = (conversation?.domain || '').toLowerCase();

  if (mode === 'teaching') {
    if (label.includes('Concept')) return 'Concept Clarification Detected';
    if (label.includes('Insight')) return 'Learning Insight Detected';
    if (label.includes('Risk')) return 'Learning Risk Detected';
  }

  if (domain.includes('sports')) {
    if (label.includes('Decision')) return 'Training Method Decision Detected';
    if (label.includes('Concept')) return 'Training Concept Detected';
    if (label.includes('Risk')) return 'Training Risk Detected';
    if (label.includes('Insight')) return 'Performance Insight Detected';
  }

  if (domain.includes('software')) {
    if (label.includes('Decision')) return 'Architecture Choice Detected';
    if (label.includes('Concept')) return 'Architecture Concern Detected';
    if (label.includes('Risk')) return 'Technical Risk Detected';
    if (label.includes('Insight')) return 'Engineering Insight Detected';
  }

  if (domain.includes('research')) {
    if (label.includes('Decision')) return 'Research Direction Detected';
    if (label.includes('Concept')) return 'Hypothesis Framing Detected';
    if (label.includes('Risk')) return 'Methodology Risk Detected';
    if (label.includes('Insight')) return 'Research Insight Detected';
  }

  if (domain.includes('education')) {
    if (label.includes('Decision')) return 'Teaching Choice Detected';
    if (label.includes('Concept')) return 'Concept Clarification Detected';
    if (label.includes('Insight')) return 'Learning Insight Detected';
  }

  return label;
};

const getSemanticAlertCopy = (label: string, conversation?: AIUpdate['conversation']) => {
  const mode = (conversation?.mode || '').toLowerCase();
  const domain = (conversation?.domain || '').toLowerCase();
  const subject = conversation?.subject || 'this topic';

  if (mode === 'teaching') {
    if (label.includes('Concept')) return `Impact: a core concept needs clearer explanation for ${subject}.`;
    if (label.includes('Insight')) return 'Impact: a useful learning pattern just emerged.';
    if (label.includes('Risk')) return 'Impact: the explanation may be losing clarity or accessibility.';
  }

  if (domain.includes('sports')) {
    if (label.includes('Decision')) return `Impact: the training approach for ${subject} needs validation.`;
    if (label.includes('Risk')) return 'Impact: training effectiveness or recovery may be affected.';
    if (label.includes('Concept')) return 'Impact: a training principle is shaping the discussion.';
    if (label.includes('Insight')) return 'Impact: a performance signal may inform the next training choice.';
  }

  if (domain.includes('software')) {
    if (label.includes('Decision')) return 'Impact: an architecture or implementation choice is forming.';
    if (label.includes('Risk')) return 'Impact: reliability, coupling, or latency could be affected.';
    if (label.includes('Concept')) return 'Impact: the design trade-off needs closer inspection.';
    if (label.includes('Insight')) return 'Impact: a technical signal can guide the next validation step.';
  }

  if (domain.includes('research')) {
    if (label.includes('Decision')) return 'Impact: the research direction or method is shifting.';
    if (label.includes('Risk')) return 'Impact: the methodology or evidence quality may be at risk.';
    if (label.includes('Concept')) return 'Impact: the hypothesis framing needs precision.';
    if (label.includes('Insight')) return 'Impact: an evidence pattern can refine the next experiment.';
  }

  if (domain.includes('education')) {
    if (label.includes('Decision')) return 'Impact: the teaching approach is being refined.';
    if (label.includes('Concept')) return 'Impact: the concept needs clearer scaffolding.';
    if (label.includes('Insight')) return 'Impact: the learner understanding may be improving.';
  }

  return formatAlertImpact(label);
};

const getSemanticAlertReason = (label: string, conversation?: AIUpdate['conversation']) => {
  const domain = (conversation?.domain || '').toLowerCase();
  const mode = (conversation?.mode || '').toLowerCase();
  const subject = conversation?.subject || 'the current topic';

  if (domain.includes('sports')) {
    if (mode === 'technical discussion') return `Because: the discussion is about ${subject} and training mechanics.`;
    if (mode === 'teaching') return `Because: the discussion is focused on explaining ${subject}.`;
  }

  if (domain.includes('software')) {
    if (mode === 'technical discussion') return `Because: architecture, coupling, or reliability cues appeared around ${subject}.`;
  }

  if (domain.includes('research')) {
    return `Because: hypothesis, method, or evidence cues appeared around ${subject}.`;
  }

  if (domain.includes('education')) {
    return `Because: the discussion appears to be clarifying understanding around ${subject}.`;
  }

  return formatAlertReason(label);
};

const highlightTranscript = (text: string) => {
  const parts = text.split(KEYWORD_REGEX);
  return parts.map((part, index) => {
    const lowered = part.toLowerCase();
    if (KEYWORD_SET.has(lowered)) {
      return <span key={`${part}-${index}`} className="keyword-highlight">{part}</span>;
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
};

const dedupeAlerts = (items: AlertItem[]) => {
  const seen = new Set<string>();
  const result: AlertItem[] = [];
  items.forEach((alert) => {
    const key = `${alert.label}-${alert.detail}`.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    result.push(alert);
  });
  return result;
};

const deriveUnderstandingSignals = (alerts: AlertItem[], summary: string, focusTerms: string[]) => {
  const points: string[] = [];

  const latestAlerts = dedupeAlerts(alerts).slice(-3);
  latestAlerts.forEach((alert) => {
    const mapped = ALERT_UNDERSTANDING[alert.label];
    if (mapped) points.push(mapped);
  });

  const summaryLower = summary.toLowerCase();
  if (summaryLower.includes('legal') || summaryLower.includes('compliance') || summaryLower.includes('jurid')) {
    points.push('Compliance concerns are part of the active decision path.');
  }
  if (summaryLower.includes('deadline') || summaryLower.includes('prazo') || summaryLower.includes('urg')) {
    points.push('Delivery timing is shaping the conversation.');
  }
  if (summaryLower.includes('decis') || summaryLower.includes('go/no-go')) {
    points.push('The group is converging toward a go/no-go style decision.');
  }

  if (focusTerms.some((term) => ['deadline', 'prazo', 'risco', 'risk', 'compliance', 'legal'].includes(term.toLowerCase()))) {
    points.push('Risk and timing signals remain active in the meeting context.');
  }

  const unique = Array.from(new Set(points));
  return unique.slice(0, 3);
};

interface AlertItem {
  emoji: string;
  label: string;
  detail: string;
}

interface AIUpdate {
  summary?: string;
  questions?: string[];
  insights?: string[];
  alerts?: AlertItem[];
  actions?: string[];
  directions?: string[];
  focusTerms?: string[];
  chunkIndex?: number;
  totalChunks?: number;
  processingTimeMs?: number;
  conversation?: {
    domain?: string;
    subject?: string;
    intent?: string;
    mode?: string;
    confidence?: number;
  };
  conversation_state?: {
    stableDomain?: string;
    emergingTopics?: string[];
    dominantIntent?: string;
    currentMode?: string;
    confidenceTrend?: number[];
    unresolvedQuestions?: string[];
    semanticTransitions?: string[];
    understandingTimeline?: string[];
    openThreads?: string[];
    topicStability?: number;
    latestSubject?: string;
  };
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'streaming';

export default function Home() {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [summary, setSummary] = useState('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  const [focusTerms, setFocusTerms] = useState<string[]>([]);
  const [liveMode, setLiveMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState<string[]>([]);
  const [partialTranscript, setPartialTranscript] = useState('');
  const [liveError, setLiveError] = useState<string | null>(null);
  const [demoRunning, setDemoRunning] = useState(false);
  const [presentationMode, setPresentationMode] = useState(false);
  const [aiThinkingText, setAiThinkingText] = useState(THINKING_MESSAGES[0]);
  const [alertTrigger, setAlertTrigger] = useState('');
  const [liveSource, setLiveSource] = useState<'microphone' | 'system' | null>(null);
  const [isSafari, setIsSafari] = useState(false);
  const [currentChunk, setCurrentChunk] = useState('');
  const [chunkInfo, setChunkInfo] = useState({ current: 0, total: 0 });
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamComplete, setStreamComplete] = useState(false);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [latestAlertKey, setLatestAlertKey] = useState(0);
  const [meetingUnderstanding, setMeetingUnderstanding] = useState<string[]>([]);
  const [liveMicroUpdate, setLiveMicroUpdate] = useState('');
  const [aiFocus, setAiFocus] = useState<string[]>([]);
  const [confidenceLabel, setConfidenceLabel] = useState<'Low'|'Medium'|'High'>('Low');
  const [missingContext, setMissingContext] = useState<string[]>([]);
  const [thinkingFeed, setThinkingFeed] = useState<string[]>([]);
  const [suggestedTopic, setSuggestedTopic] = useState('');
  const [conversationMeta, setConversationMeta] = useState<AIUpdate['conversation'] | null>(null);
  const [conversationState, setConversationState] = useState<AIUpdate['conversation_state'] | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const speechRecognitionRef = useRef<any>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      setStatus('connected');
      setDemoRunning(false);
      socket.send(JSON.stringify({ type: 'stop_simulated' }));
    };

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };

    socket.onclose = () => {
      setStatus('disconnected');
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    socket.onerror = () => {
      socket.close();
    };
  }, []);

  const handleMessage = (msg: Record<string, unknown>) => {
    switch (msg.type) {
      case 'connected':
        setStatus('connected');
        break;

      case 'chunk':
        setStatus('streaming');
        setCurrentChunk(String(msg.chunk || ''));
        setChunkInfo({
          current: Number(msg.chunkIndex || 0),
          total: Number(msg.totalChunks || 0),
        });
        setIsProcessing(true);
        setStreamComplete(false);
        if (!liveMode) setDemoRunning(true);
        break;

      case 'ai_update': {
        const update = msg as AIUpdate;
        setIsProcessing(false);
        if (update.processingTimeMs !== undefined) setProcessingTime(update.processingTimeMs);
        if (update.summary) setSummary(update.summary);
        if (update.questions) setQuestions(update.questions);
        if (update.insights) setInsights(update.insights);
        if (update.actions || update.directions) setActions(update.actions || update.directions || []);
        if (update.focusTerms) setFocusTerms(update.focusTerms);
        if (update.conversation) setConversationMeta(update.conversation);
        if (update.conversation_state) setConversationState(update.conversation_state);
        if (update.alerts) {
          setAlerts(update.alerts);
          if (update.alerts.length > 0) {
            // Bump key to re-trigger the flash animation on the latest alert
            setLatestAlertKey((k) => k + 1);
            const latest = update.alerts[update.alerts.length - 1];
            setAlertTrigger(latest?.detail || '');
          }
        }
        break;
      }

      case 'transcript_update': {
        const text = String(msg.text || '').trim();
        const isFinal = msg.isFinal !== false;
        if (!text) break;
        if (isFinal) {
          setLiveTranscript((prev) => [...prev, text].slice(-8));
          setPartialTranscript('');
        } else {
          setPartialTranscript(text);
        }
        break;
      }

      case 'system_status':
        setLiveMode(Boolean(msg.liveMode));
        break;

      case 'stream_complete':
        setStatus('connected');
        if (!liveMode) setStreamComplete(true);
        setDemoRunning(false);
        setIsProcessing(false);
        setCurrentChunk('');
        break;

      default:
        break;
    }
  };

  useEffect(() => {
    // detect Safari for helpful UX hints
    try {
      const ua = navigator.userAgent || '';
      const safari = /version\/.+? safari\//i.test(ua) && !/chrome|chromium|edg|opr/i.test(ua);
      setIsSafari(Boolean(safari));
    } catch (e) {
      setIsSafari(false);
    }
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
      stopLiveMode();
    };
  }, [connect]);

  useEffect(() => {
    if (isProcessing) {
      let index = 0;
      setAiThinkingText(THINKING_MESSAGES[index]);
      const timer = setInterval(() => {
        index = (index + 1) % THINKING_MESSAGES.length;
        setAiThinkingText(THINKING_MESSAGES[index]);
      }, 1600);
      return () => clearInterval(timer);
    }

    if (liveMode && isListening) {
      let index = 0;
      setAiThinkingText(`🎤 ${LISTENING_MESSAGES[index]}`);
      const timer = setInterval(() => {
        index = (index + 1) % LISTENING_MESSAGES.length;
        setAiThinkingText(`🎤 ${LISTENING_MESSAGES[index]}`);
      }, 2200);
      return () => clearInterval(timer);
    }

    if (liveMicroUpdate) {
      setAiThinkingText(liveMicroUpdate);
      return undefined;
    }

    if (alerts.length > 0 || actions.length > 0) {
      setAiThinkingText('Decision support ready.');
      return undefined;
    }

    if (demoRunning) {
      setAiThinkingText('Demo running. Waiting for signals...');
      return undefined;
    }

    setAiThinkingText('AI is standing by...');
    return undefined;
  }, [isProcessing, liveMode, isListening, demoRunning, alerts.length, actions.length, liveMicroUpdate]);

  useEffect(() => {
    const nextSignals = deriveUnderstandingSignals(alerts, summary, focusTerms);
    if (nextSignals.length === 0) return;

    setMeetingUnderstanding((prev) => {
      const merged = Array.from(new Set([...prev, ...nextSignals]));
      return merged.slice(-3);
    });

    const latestSignal = nextSignals[0];
    setLiveMicroUpdate(`AI now believes: ${latestSignal}`);
  }, [alerts, summary, focusTerms]);

  useEffect(() => {
    if (!conversationState) return;

    const timeline = conversationState.understandingTimeline || [];
    const transitions = conversationState.semanticTransitions || [];
    const unresolved = conversationState.unresolvedQuestions || [];
    const threads = conversationState.openThreads || [];

    const feed: string[] = [];
    if (timeline.length > 0) feed.push(...timeline.slice(-3));
    if (transitions.length > 0) feed.push(transitions[transitions.length - 1]);
    if (threads.length > 0) feed.push(`Open thread: ${threads[0]}`);
    if (unresolved.length > 0) feed.push(`Unresolved question: ${unresolved[0]}`);

    if (feed.length > 0) {
      setMeetingUnderstanding((prev) => Array.from(new Set([...prev, ...feed])).slice(-4));
      setThinkingFeed((prev) => Array.from(new Set([...feed.slice(-2), ...prev])).slice(0, 4));
    }
  }, [conversationState]);

  // --- Cognitive UI: focus, confidence, missing context, thinking feed ---
  const computeAiFocus = (alertsList: AlertItem[], terms: string[], summaryText: string) => {
    // Domain-aware focus candidates
    const domain = (conversationState?.stableDomain || conversationMeta?.domain || 'general').toLowerCase();
    const focus: string[] = [];

    const domainCandidates: Record<string, string[]> = {
      'sports': [
        'whether isolated exercises improve neural activation',
        'how movement complexity impacts muscle recruitment',
        'the effect of exercise order on motor learning',
      ],
      'sports science': [
        'whether isolated exercises improve neural activation',
        'how movement complexity impacts muscle recruitment',
        'the effect of exercise order on motor learning',
      ],
      'software engineering': [
        'scalability bottlenecks',
        'event consistency risks',
        'service coupling impact',
      ],
      'research': [
        'primary hypothesis and measurable outcomes',
        'experimental controls and validity',
        'statistical power and sample requirements',
      ],
      'education': [
        'student proficiency levels',
        'learning objectives clarity',
        'evaluation/assessment criteria',
      ],
      'legal': [
        'applicable regulations and jurisdiction',
        'required compliance artifacts',
        'contractual obligations affecting the outcome',
      ],
      'product': [
        'who owns the final decision',
        'market differentiation requirements',
        'launch readiness criteria',
      ],
      'general': [
        'what the main objective of this discussion is',
        'which stakeholders are involved',
        'what success looks like for this topic',
      ],
    };

    const candidates = domainCandidates[domain] || domainCandidates['general'];

    // If explicit signals exist, promote related candidates
    const alertLabels = new Set(alertsList.map((a) => a.label.toLowerCase()));
    if (alertLabels.has('key decision detected'.toLowerCase())) {
      // decision-like behavior: pick ownership or decision-relevant focus
      if (domain === 'product' || domain === 'general') focus.push('who owns the final decision');
      else focus.push(candidates[0]);
    }

    // keyword-driven enhancements
    const s = summaryText.toLowerCase();
    if (s.includes('hypothesis') || s.includes('experiment') || conversationMeta?.intent?.toLowerCase()?.includes('research') || conversationState?.dominantIntent?.toLowerCase()?.includes('research')) {
      focus.push(...(domainCandidates['research']));
    }

    // always include top domain candidates as primary focus
    focus.push(...candidates.slice(0, 4));

    // dedupe and limit
    const unique = Array.from(new Set(focus));
    return unique.slice(0, 4);
  };

  const computeConfidence = (alertsList: AlertItem[], summaryText: string, terms: string[]) => {
    const uniqueSignals = dedupeAlerts(alertsList).length + (terms.length > 0 ? 1 : 0) + (summaryText ? 1 : 0);
    if (uniqueSignals >= 3) return 'High' as const;
    if (uniqueSignals === 2) return 'Medium' as const;
    return 'Low' as const;
  };

  const computeMissing = (summaryText: string, terms: string[]) => {
    const needs = [] as string[];
    const s = summaryText.toLowerCase();
    const domain = (conversationState?.stableDomain || conversationMeta?.domain || 'general').toLowerCase();

    const domainNeeds: Record<string, string[]> = {
      'sports': ['athlete experience level', 'target muscle group', 'training goal (strength vs hypertrophy)'],
      'sports science': ['athlete experience level', 'target muscle group', 'training goal (strength vs hypertrophy)'],
      'education': ['student proficiency level', 'learning objective', 'evaluation criteria'],
      'software engineering': ['expected load and SLA', 'data consistency requirements', 'auth and failure modes'],
      'research': ['primary hypothesis', 'measurement plan', 'sample size / statistical power'],
      'legal': ['applicable regulation', 'contractual constraints', 'required approvals'],
      'product': ['final decision owner', 'approval deadline', 'market launch criteria'],
      'general': ['clarify the primary objective', 'identify stakeholders', 'define success criteria'],
    };

    const candidates = domainNeeds[domain] || domainNeeds['general'];
    // prefer explicit mentions from summary or terms
    if (s.includes('athlete') || terms.some(t=>/athlete|training|reps/i.test(t))) {
      needs.push('athlete experience level');
    }
    if (s.includes('deadline') || terms.some(t=>/deadline|prazo/i.test(t))) {
      needs.push('approval deadline');
    }

    // then fill from domain candidates
    needs.push(...candidates);
    return Array.from(new Set(needs)).slice(0, 4);
  };

  const pushThinking = (entry: string) => {
    setThinkingFeed(prev => {
      const next = [entry, ...prev].slice(0, 4);
      return next;
    });
  };

  useEffect(() => {
    const newFocus = computeAiFocus(alerts, focusTerms, summary);
    setAiFocus(newFocus);

    const newConfidence = computeConfidence(alerts, summary, focusTerms);
    setConfidenceLabel((prev) => {
      if (prev !== newConfidence) {
        pushThinking(`Confidence ${newConfidence} — updated by recent signals.`);
      }
      return newConfidence;
    });

    const missing = computeMissing(summary, focusTerms);
    setMissingContext(missing);

    // suggested topic: highest-priority missing context, but domain-aware labels
    if (missing.length > 0) {
      const topic = conversationMeta?.domain
        ? `${conversationMeta.domain}: clarify ${missing[0]}`
        : `Clarify: ${missing[0]}`;
      setSuggestedTopic(topic);
    } else if (newFocus.length > 0) {
      setSuggestedTopic(conversationMeta?.domain ? `${conversationMeta.domain}: deepen ${newFocus[0]}` : `Deepen: ${newFocus[0]}`);
    } else {
      setSuggestedTopic(conversationMeta?.domain ? `${conversationMeta.domain}: open clarification` : 'Open: clarify ownership or timeline.');
    }

    // push subtle thinking feed entries when understanding updates
    if (meetingUnderstanding.length > 0) {
      pushThinking(`Updated understanding: ${meetingUnderstanding[meetingUnderstanding.length - 1]}`);
    }
  }, [alerts, focusTerms, summary, meetingUnderstanding]);

  const sendMessage = (payload: Record<string, unknown>) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    ws.current.send(JSON.stringify(payload));
  };

  const resetSessionState = () => {
    setSummary('');
    setQuestions([]);
    setInsights([]);
    setAlerts([]);
    setActions([]);
    setFocusTerms([]);
    setLiveTranscript([]);
    setPartialTranscript('');
    setAlertTrigger('');
    setStreamComplete(false);
    setCurrentChunk('');
    setChunkInfo({ current: 0, total: 0 });
    setProcessingTime(null);
    setMeetingUnderstanding([]);
    setLiveMicroUpdate('');
    setConversationMeta(null);
    setConversationState(null);
  };

  const blobToBase64 = (blob: Blob) => new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = reader.result;
      if (typeof result === 'string') {
        const base64 = result.split(',')[1] || '';
        resolve(base64);
      } else {
        reject(new Error('Failed to read blob'));
      }
    };
    reader.onerror = () => reject(new Error('Failed to read blob'));
    reader.readAsDataURL(blob);
  });

  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setLiveError('This browser does not support speech recognition. Please use Chrome or choose Browser Audio.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'pt-BR';

    recognition.onresult = (event: any) => {
      let interim = '';
      let finalText = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0]?.transcript || '';
        if (event.results[i].isFinal) {
          finalText += `${transcript} `;
        } else {
          interim += transcript;
        }
      }

      if (interim.trim()) {
        setPartialTranscript(interim.trim());
      }

      const cleaned = finalText.trim();
      if (cleaned) {
        setLiveTranscript((prev) => [...prev, cleaned].slice(-8));
        setPartialTranscript('');
        sendMessage({ type: 'text_chunk', text: cleaned, isFinal: true });
      }
    };

    recognition.onerror = () => {
      setLiveError('We could not keep microphone transcription active. Please try Browser Audio or restart Live mode.');
    };

    recognition.start();
    speechRecognitionRef.current = recognition;
  };

  const startLiveMode = async (source: 'microphone' | 'system') => {
    if (liveMode) return;
    setLiveError(null);
    try {
      let stream: MediaStream;
      if (source === 'system') {
        if (!navigator.mediaDevices.getDisplayMedia) {
          setLiveError('Browser audio capture is limited here. Please use Chrome or choose Microphone mode.');
          return;
        }
        stream = await navigator.mediaDevices.getDisplayMedia({ audio: true, video: true });
      } else {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      if (stream.getAudioTracks().length === 0) {
        stream.getTracks().forEach((track) => track.stop());
        setLiveError('We could not detect browser audio. You can switch to Microphone mode for a stable live experience.');
        return;
      }
      audioStreamRef.current = stream;
      const preferredType = 'audio/webm';
      const recorder = MediaRecorder.isTypeSupported(preferredType)
        ? new MediaRecorder(stream, { mimeType: preferredType })
        : new MediaRecorder(stream);
      recorder.ondataavailable = async (event) => {
        if (!event.data || event.data.size === 0) return;
        try {
          const base64 = await blobToBase64(event.data);
          sendMessage({ type: 'audio_chunk', payload: base64, mimeType: event.data.type });
        } catch (err) {
          console.warn('[Audio] Failed to encode chunk');
        }
      };
      recorder.start(250);
      mediaRecorderRef.current = recorder;
      setLiveMode(true);
      setIsListening(true);
      setDemoRunning(false);
      setStreamComplete(false);
      setLiveSource(source);
      resetSessionState();
      sendMessage({ type: 'start_live' });
      if (source === 'microphone') {
        startSpeechRecognition();
      }
    } catch (err) {
      setLiveError(source === 'system'
        ? 'Browser audio permission was not granted. You can try again or switch to Microphone mode.'
        : 'Microphone permission was not granted. Please allow access and try again.');
      setLiveMode(false);
      setIsListening(false);
    }
  };

  const stopLiveMode = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    if (speechRecognitionRef.current) {
      speechRecognitionRef.current.stop();
      speechRecognitionRef.current = null;
    }
    setIsListening(false);
    setLiveMode(false);
    setLiveSource(null);
    setLiveError(null);
    sendMessage({ type: 'stop_live' });
  };

  const startDemo = () => {
    stopLiveMode();
    setLiveError(null);
    setDemoRunning(true);
    setStreamComplete(false);
    resetSessionState();
    sendMessage({ type: 'start_simulated' });
  };

  const stopDemo = () => {
    setDemoRunning(false);
    sendMessage({ type: 'stop_simulated' });
  };

  const isIdle = !demoRunning && !liveMode && !isListening;
  const hasDecisionSupport = alerts.length > 0 || actions.length > 0;
  const hasSessionContent = Boolean(summary)
    || alerts.length > 0
    || actions.length > 0
    || liveTranscript.length > 0
    || Boolean(partialTranscript);
  const journeyState = isIdle
    ? 'idle'
    : hasDecisionSupport
      ? 'decision'
      : isProcessing
        ? 'processing'
        : (liveMode && isListening)
          ? 'listening'
          : 'idle';

  const displayAlerts = dedupeAlerts(alerts).slice(-3).reverse();
  const latestAlert = displayAlerts.length > 0 ? displayAlerts[0] : null;
  const latestAlertLabel = latestAlert ? getSemanticAlertTitle(latestAlert.label, conversationMeta || undefined) : '';
  const latestAlertImpact = latestAlert ? getSemanticAlertCopy(latestAlert.label, conversationMeta || undefined) : '';
  const latestAlertReason = latestAlert ? getSemanticAlertReason(latestAlert.label, conversationMeta || undefined) : '';
  const primaryAction = actions.length > 0 ? actions[0].replace(/^→/, '').trim() : '';
  const secondaryActions = actions.slice(1, 2).map((item) => item.replace(/^→/, '').trim());
  const triggerKey = alertTrigger.slice(0, 24).toLowerCase();
  const actionEmptyText = isIdle
    ? 'Start a session to see contextual guidance.'
    : conversationMeta?.mode === 'teaching'
      ? 'Waiting for a concept that needs clarification...'
      : conversationMeta?.mode === 'brainstorming'
        ? 'Waiting for a useful hypothesis or direction...'
        : conversationMeta?.mode === 'technical discussion'
          ? 'Waiting for a validation target or technical constraint...'
          : 'Waiting for a clear next step...';

  return (
    <div className="container">
      <div className={`mode-banner ${liveMode ? 'is-live' : demoRunning ? 'is-sim' : 'is-idle'}`}>
        <div className="mode-banner-title">
          {liveMode ? 'LIVE MODE' : demoRunning ? 'SIMULATION MODE' : 'IDLE'}
        </div>
        <div className="mode-banner-subtitle">
          {liveMode
            ? 'Listening now and turning speech into decisions.'
            : demoRunning
              ? 'Demo running. End the session to restart or switch.'
              : 'Idle. Start Demo or Live Meeting Copilot to begin.'}
        </div>
      </div>

      <div className="header">
        <h1>AI Streaming Copilot - Live Decision Intelligence</h1>
        <p>Streaming + agents + RAG. O sistema entende o que acontece em tempo real.</p>
      </div>

      {isIdle ? (
        <div className="session-start">
          <div className="session-start-header">
            <h2>Start a session</h2>
            <p>Choose the source. The AI starts only when you choose a mode.</p>
          </div>
          <div className="session-source-grid">
            <button className="session-source-card" onClick={startDemo}>
              <span className="session-source-title">Demo Script</span>
              <span className="session-source-desc">Reliable scripted flow for live presentations</span>
            </button>

            <button
              className="session-source-card"
              onClick={() => startLiveMode('microphone')}
              disabled={status === 'disconnected' || status === 'connecting'}
            >
              <span className="session-source-title">Live Microphone</span>
              <span className="session-source-desc">Recommended for presentations</span>
            </button>

            <button
              className="session-source-card session-source-card--primary"
              onClick={() => startLiveMode('system')}
              disabled={status === 'disconnected' || status === 'connecting'}
            >
              <span className="session-source-title">Browser Audio</span>
              <span className="session-source-desc">Best for meetings/videos (Chrome preferred)</span>
            </button>
          </div>

          {isSafari && (
            <div className="live-setup-hint live-setup-warning">
              Safari limits browser audio capture. For the best live experience, use Chrome or microphone mode.
            </div>
          )}

          {liveError && (
            <div className="fallback-container">
              <div className="control-error">{liveError}</div>
              <button className="control-button" onClick={() => startLiveMode('microphone')}>
                Switch to microphone mode
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="control-bar">
          <div className="control-status">
            <span className={`control-pill ${liveMode ? 'is-live' : 'is-simulated'}`}>
              {liveMode ? 'LIVE MODE' : 'SIMULATION MODE'}
            </span>
            {isListening && <span className="control-pill is-listening">Listening...</span>}
            {isProcessing && <span className="control-pill is-processing">Processing</span>}
            {liveSource && (
              <span className="control-pill is-source">
                {liveSource === 'system' ? 'System Audio' : 'Microphone'}
              </span>
            )}
            {liveError && (
              <span className="control-error">{liveError}</span>
            )}
          </div>
          <div className="control-actions">
            {liveMode && (
              <button className="control-button" onClick={stopLiveMode}>
                Stop Live
              </button>
            )}
            {demoRunning && (
              <button className="control-button ghost" onClick={stopDemo}>
                Stop Demo
              </button>
            )}
            <button className="control-button ghost" onClick={() => setPresentationMode((prev) => !prev)}>
              {presentationMode ? 'Exit Presentation' : 'Presentation Mode'}
            </button>
          </div>
        </div>
      )}

      {!presentationMode && (
        <div className="journey">
          <div className={`journey-step ${journeyState === 'idle' ? 'active' : ''}`}>Idle</div>
          <div className={`journey-step ${journeyState === 'listening' ? 'active' : ''}`}>Listening</div>
          <div className={`journey-step ${journeyState === 'processing' ? 'active' : ''}`}>Processing</div>
          <div className={`journey-step ${journeyState === 'decision' ? 'active' : ''}`}>Decision Support</div>
        </div>
      )}

      <div className="thinking-dock">
        <span className="thinking-icon">🧠</span>
        <span className="thinking-text">{aiThinkingText}</span>
      </div>


      {(!isIdle || hasSessionContent) && (
        <>
          {!presentationMode && liveMicroUpdate && (
            <div className="micro-update-banner">{liveMicroUpdate}</div>
          )}

          <div className="live-copilot-grid">
            <div className="copilot-card understanding-card">
              <div className="copilot-card-header">AI Conversation Understanding</div>
              <div className="understanding-compact">
                  <div className="understanding-row"><strong>Domain:</strong> {conversationState?.stableDomain || conversationMeta?.domain || 'General'}</div>
                  <div className="understanding-row"><strong>Intent:</strong> {conversationState?.dominantIntent || conversationMeta?.intent || 'Exploration'}</div>
                  <div className="understanding-row"><strong>Mode:</strong> {conversationState?.currentMode || conversationMeta?.mode || 'Analysis'}</div>
                  <div className="understanding-row"><strong>Subject:</strong> {conversationMeta?.subject || conversationState?.latestSubject || 'unspecified'}</div>
                  <div className="understanding-row"><strong>Confidence:</strong> {conversationMeta?.confidence ? `${Math.round((conversationMeta.confidence||0)*100)}%` : confidenceLabel}</div>
              </div>
                <div className="understanding-summary">
                  {(() => {
                    const trend = conversationState?.confidenceTrend || [];
                    if (trend.length < 2) return 'The AI is accumulating evidence before changing its interpretation.';
                    const delta = trend[trend.length - 1] - trend[0];
                    if (delta > 0.12) return 'AI confidence increased over time.';
                    if (delta < -0.12) return 'Topic stability decreased after subject transition.';
                    return 'AI confidence is holding steady while the conversation evolves.';
                  })()}
                </div>
                {(conversationState?.semanticTransitions || []).length > 0 && (
                  <div className="understanding-timeline">
                    <div className="timeline-title">Understanding Evolution</div>
                    {(conversationState?.semanticTransitions || []).slice(-3).map((item) => (
                      <div className="timeline-item" key={item}>• {item}</div>
                    ))}
                  </div>
                )}
              <div className="understanding-body">
                {(meetingUnderstanding.length > 0 ? meetingUnderstanding.slice(-3) : [
                  'The AI is still building initial meeting context.',
                ]).map((item) => (
                  <div className="understanding-item" key={item}>• {item}</div>
                ))}
              </div>
                {(conversationState?.openThreads || []).length > 0 && (
                  <div className="open-thread-block">
                    <div className="open-thread-title">Open cognitive threads</div>
                    <div className="open-thread-copy">The AI is still trying to understand:</div>
                    <ul className="open-thread-list">
                      {(conversationState?.openThreads || []).slice(-3).map((thread) => (
                        <li key={thread}>{thread}</li>
                      ))}
                    </ul>
                  </div>
                )}
              {!presentationMode && (
                <div className="context-summary">
                  {summary ? summary : 'Understanding will deepen as the conversation evolves.'}
                </div>
              )}
            </div>

            <div className="copilot-card focus-card">
              <div className="copilot-card-header">{getSemanticModeLabel(conversationMeta?.mode)}</div>
              <div className="focus-body" style={{padding: '12px 14px'}}>
                <div className="confidence-row">
                  <div className={`confidence-pill confidence-${confidenceLabel.toLowerCase()}`}>{confidenceLabel} confidence</div>
                  <div className="suggested-topic">{suggestedTopic}</div>
                </div>
                <div className="focus-list" style={{marginTop:8}}>
                  {aiFocus.map((f)=> (<div key={f} className="focus-item">• {f}</div>))}
                </div>

                <div className="missing-context" style={{marginTop:12}}>
                  <div className="copilot-card-header" style={{fontSize:'0.68rem'}}>Missing Context</div>
                  {missingContext.length === 0 ? (
                    <div className="missing-empty">No immediate gaps detected.</div>
                  ) : (
                    <ul className="missing-list">
                      {missingContext.map((m)=> (<li key={m}>{m}</li>))}
                    </ul>
                  )}
                </div>
                <div className="thinking-feed" aria-live="polite" style={{marginTop:10}}>
                  {thinkingFeed.map((t, i) => (
                    <div key={`${t}-${i}`} className={`thinking-entry entry-${i}`}>• {t}</div>
                  ))}
                </div>
              </div>
            </div>

            <div className="copilot-card action-hero">
              <div className="action-hero-header">
                <span>{conversationMeta?.mode === 'teaching' ? 'Suggested Explanation' : conversationMeta?.mode === 'brainstorming' ? 'Suggested Ideas' : conversationMeta?.mode === 'decision making' ? 'Action Recommendation' : conversationMeta?.mode === 'technical discussion' ? 'Validation Recommendation' : 'Recommended Action'}</span>
                <span className="action-hero-badge">Action Agent</span>
              </div>
              {primaryAction ? (
                <div>
                  <div className="action-justification" style={{fontSize:'0.9rem', color:'#cfeef8', marginBottom:6}}>
                    {conversationMeta ? `Because the discussion focuses on ${conversationMeta.subject || conversationMeta.domain || 'this domain'}, the AI recommends:` : ''}
                  </div>
                  <div className="action-hero-primary">{primaryAction}</div>
                </div>
              ) : (
                <div className="action-hero-empty">{actionEmptyText}</div>
              )}
              {!presentationMode && secondaryActions.length > 0 && (
                <div className="action-hero-secondary">
                  {secondaryActions.map((item) => (
                    <span key={item}>{item}</span>
                  ))}
                </div>
              )}
            </div>

            <div className="copilot-card risk-card" key={latestAlertKey}>
              <div className="copilot-card-header">{conversationMeta?.mode === 'teaching' ? 'Open Learning Uncertainty' : conversationMeta?.mode === 'brainstorming' ? 'Emerging Tension' : conversationMeta?.mode === 'technical discussion' ? 'Architecture Concern' : conversationMeta?.mode === 'decision making' ? 'Decision Signal' : 'Open Risk / Signal'}</div>
              {latestAlert ? (
                <div className={`risk-highlight severity-${getAlertSeverity(latestAlert.label)}`}>
                  <div className="decision-card-header">
                    <span className="alert-emoji">{latestAlert.emoji}</span>
                    <span className="decision-title">{latestAlertLabel}</span>
                  </div>
                  <div className="decision-section">
                    <span className="decision-label">{conversationMeta?.mode === 'teaching' ? 'Why this matters' : conversationMeta?.mode === 'brainstorming' ? 'Why the idea is emerging' : conversationMeta?.mode === 'technical discussion' ? 'Why it matters technically' : 'Why this matters'}</span>
                    <span className="decision-text">{latestAlertImpact}</span>
                  </div>
                  <div className="decision-section">
                    <span className="decision-label">{conversationMeta?.mode === 'teaching' ? 'Clue' : conversationMeta?.mode === 'brainstorming' ? 'Cue' : conversationMeta?.mode === 'technical discussion' ? 'Signal' : 'Signal'}</span>
                    <span className="decision-text">{latestAlert.detail ? `"${latestAlert.detail}"` : latestAlertReason}</span>
                  </div>
                </div>
              ) : (
                <div className="action-hero-empty">No domain-specific signal yet.</div>
              )}
            </div>
          </div>

          {/* Transcript moved below to de-emphasize it visually */}
          <div className="copilot-card live-transcript small" id="live-transcript-card">
            <div className="live-transcript-header">
              <span>Live Transcript (support)</span>
              <span className={`live-transcript-status ${liveMode ? 'on' : 'off'}`}>
                {liveMode
                  ? `LIVE • ${liveSource === 'system' ? 'BROWSER' : 'MIC'}`
                  : 'IDLE'}
              </span>
            </div>
            <div className="live-transcript-body">
              {liveTranscript.length === 0 && !partialTranscript && (
                <div className="empty-state">Waiting for speech...</div>
              )}
              {liveTranscript.map((line, index) => {
                const isTrigger = triggerKey && line.toLowerCase().includes(triggerKey);
                return (
                  <div
                    key={`${line}-${index}`}
                    className={`live-transcript-line ${isTrigger ? 'trigger-highlight' : ''}`}
                  >
                    {highlightTranscript(line)}
                  </div>
                );
              })}
              {partialTranscript && (
                <div className="live-transcript-partial">
                  🎤 {highlightTranscript(partialTranscript)}
                </div>
              )}
            </div>
          </div>

          {streamComplete && !presentationMode && (
            <div className="stream-complete">
              ✅ Stream ended - {alerts.length} key moment{alerts.length !== 1 ? 's' : ''} captured.
            </div>
          )}
        </>
      )}
    </div>
  );
}
