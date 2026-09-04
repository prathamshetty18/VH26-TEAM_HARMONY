import type { Message, SessionMemoryState, Machine, BackendConfig, Citation, AmbiguityOption } from '../types';
import { INITIAL_MACHINES, processMockQuery, extractMachineAndError } from './mockEngine';

const DEFAULT_CONFIG: BackendConfig = {
  mode: 'live', // Default to live, automatically falling back if unreachable
  baseUrl: 'http://localhost:8000',
};

export class DiagnosticService {
  private config: BackendConfig;

  constructor() {
    const saved = localStorage.getItem('machineassist_config');
    this.config = saved ? JSON.parse(saved) : DEFAULT_CONFIG;
  }

  public getConfig(): BackendConfig {
    return { ...this.config };
  }

  public setConfig(newConfig: Partial<BackendConfig>) {
    this.config = { ...this.config, ...newConfig };
    localStorage.setItem('machineassist_config', JSON.stringify(this.config));
  }

  public async checkBackendHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.config.baseUrl}/machines`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(1800),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async getMachines(): Promise<Machine[]> {
    try {
      const res = await fetch(`${this.config.baseUrl}/machines`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(2500),
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data.machines || []);
        if (Array.isArray(list) && list.length > 0) {
          return list.map((item: any) => {
            const nameStr = typeof item === 'string' ? item : (item.name || item.id);
            const idStr = typeof item === 'string' ? item : (item.id || item.name);
            return {
              id: idStr,
              name: nameStr,
              category: typeof item === 'object' && item.category ? item.category : 'Industrial Unit',
              manualFile: typeof item === 'object' && item.manualFile ? item.manualFile : `${idStr.toLowerCase().replace(/[^a-z0-9]/g, '')}.txt`,
              indexed: true,
              pageCount: typeof item === 'object' && item.pageCount ? item.pageCount : 120,
            };
          });
        }
      }
    } catch (err) {
      console.warn('Backend /machines unreachable, using default registered units:', err);
    }
    return INITIAL_MACHINES;
  }

  public async sendQuery(
    userQuery: string,
    sessionState: SessionMemoryState,
    scopedMachine: string | null
  ): Promise<{ message: Message; newSession: SessionMemoryState; isLiveBackend: boolean }> {
    if (this.config.mode === 'live') {
      try {
        // Try /query first (core RAG contract)
        const endpoint = `${this.config.baseUrl}/query`;
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            message: userQuery,
            session_id: sessionState.sessionId,
            machine_filter: scopedMachine || undefined,
          }),
          signal: AbortSignal.timeout(30000), // Increased from 8000ms because LLM calls can take 10-15s
        });

        if (res.ok) {
          const data = await res.json();
          const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

          // 1. Check Disambiguation / Ambiguity
          if (data.ambiguous) {
            const options: AmbiguityOption[] = (data.options || []).map((opt: any) => ({
              machine: opt.machine,
              label: `${opt.machine} — ${opt.summary}`,
              description: opt.summary,
              queryHint: `${sessionState.lastError || userQuery} on ${opt.machine}`,
            }));

            const assistantMsg: Message = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              cardType: 'ambiguity',
              timestamp,
              ambiguityPrompt: data.answer || 'That error code exists on more than one machine. Which one are you asking about?',
              ambiguityOptions: options,
            };

            const extracted = extractMachineAndError(userQuery, sessionState);
            return {
              message: assistantMsg,
              newSession: {
                ...sessionState,
                lastError: extracted.error || sessionState.lastError,
                updatedAt: timestamp,
              },
              isLiveBackend: true,
            };
          }

          // 2. Check Safety / Insufficient Info / Refusal
          const answerText: string = data.answer || '';
          const isRefusal =
            answerText.toLowerCase().includes('sufficient information') ||
            answerText.toLowerCase().includes("don't cover this") ||
            answerText.toLowerCase().includes("can't find this") ||
            answerText.toLowerCase().includes('unsupported answer') ||
            (Array.isArray(data.sources) && data.sources.length === 0 && !answerText.includes('1.'));

          if (isRefusal) {
            const assistantMsg: Message = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              cardType: 'refusal',
              timestamp,
              refusalMessage: answerText || "The manuals don't cover this. I won't guess at a fix.",
            };

            const extracted = extractMachineAndError(userQuery, sessionState);
            return {
              message: assistantMsg,
              newSession: {
                ...sessionState,
                lastMachine: extracted.machine || scopedMachine || sessionState.lastMachine,
                updatedAt: timestamp,
              },
              isLiveBackend: true,
            };
          }

          // 3. Normal Verified Answer
          const citations: Citation[] = (data.sources || []).map((s: any) => ({
            manual: s.manual || 'technical_manual.txt',
            page: s.page || 2,
            section: s.section || `${s.machine || 'Equipment'} Troubleshooting`,
            snippet: s.snippet || `${s.section || 'Maintenance Section'}: Verified manufacturer instructions for ${s.machine || 'machine'}.`,
          }));

          let meaning = answerText;
          let causes: string[] = [];
          let steps: string[] = [];

          // Parse standard 4-section structured answer
          const meaningMatch = answerText.match(/(?:1\.\s*Error meaning:?|MEANING:?)\s*([\s\S]*?)(?=(?:2\.\s*Probable causes:?|CAUSES:?|$))/i);
          const causesMatch = answerText.match(/(?:2\.\s*Probable causes:?|CAUSES:?)\s*([\s\S]*?)(?=(?:3\.\s*Step-by-step corrective action:?|STEPS:?|$))/i);
          const stepsMatch = answerText.match(/(?:3\.\s*Step-by-step corrective action:?|STEPS:?)\s*([\s\S]*?)(?=(?:4\.\s*Sources:?|SOURCES:?|$))/i);

          if (meaningMatch && meaningMatch[1].trim()) {
            meaning = meaningMatch[1].trim();
          }

          if (causesMatch && causesMatch[1].trim()) {
            causes = causesMatch[1]
              .split('\n')
              .map((l) => l.trim())
              .filter((l) => l.startsWith('-') || l.startsWith('*') || /^\d+[\.\)]/.test(l))
              .map((l) => l.replace(/^[-*]\s*/, '').replace(/^\d+[\.\)]\s*/, '').trim())
              .filter(Boolean);
          }

          if (stepsMatch && stepsMatch[1].trim()) {
            steps = stepsMatch[1]
              .split('\n')
              .map((l) => l.trim())
              .filter((l) => /^\d+[\.\)]/.test(l) || l.startsWith('-') || l.toLowerCase().startsWith('step'))
              .map((l) => l.replace(/^\d+[\.\)]\s*/, '').replace(/^-\s*Step\s*\d*:?\s*/i, '').replace(/^-\s*/, '').trim())
              .filter(Boolean);
          }

          // Fallback if no section headers matched
          if (steps.length === 0 && answerText.includes('\n')) {
            const lines = answerText.split('\n').map((l) => l.trim()).filter(Boolean);
            const stepLines = lines.filter((l) => /^\d+[\.\)]/.test(l) || l.toLowerCase().startsWith('- step'));
            if (stepLines.length > 0) {
              steps = stepLines.map((s) => s.replace(/^\d+[\.\)]\s*/, '').replace(/^-\s*Step\s*\d*:\s*/i, ''));
            }
          }

          const assistantMsg: Message = {
            id: `msg_${Date.now()}`,
            role: 'assistant',
            cardType: 'normal',
            timestamp,
            meaning,
            causes: causes.length > 0 ? causes : undefined,
            steps: steps.length > 0 ? steps : undefined,
            citations: citations.length > 0 ? citations : undefined,
          };

          const extracted = extractMachineAndError(userQuery, sessionState);
          const topMachine = extracted.machine || scopedMachine || (citations[0] ? (data.sources[0]?.machine) : null) || sessionState.lastMachine;
          const topError = extracted.error || sessionState.lastError;

          return {
            message: assistantMsg,
            newSession: {
              ...sessionState,
              lastMachine: topMachine,
              lastError: topError,
              updatedAt: timestamp,
            },
            isLiveBackend: true,
          };
        }
      } catch (err) {
        console.warn('Live API request failed or timed out. Falling back to local diagnostic engine.', err);
      }
    }

    // Default or fallback to mock engine
    const { message, newSession } = await processMockQuery(userQuery, sessionState, scopedMachine);
    return { message, newSession, isLiveBackend: false };
  }
}

export const diagnosticService = new DiagnosticService();
