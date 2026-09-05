export interface Machine {
  id: string;
  name: string;
  category: string;
  manualFile: string;
  indexed: boolean;
  pageCount: number;
}

export interface Diagram {
  title: string;
  filename: string;
  url: string;
  caption: string;
  system?: string;
}

export interface Citation {
  manual: string; // e.g. cnc100.txt
  page: number;   // e.g. 4
  section?: string; // e.g. E101 Troubleshooting - Spindle Overheat
  snippet?: string;
  diagram_url?: string;
  diagram_title?: string;
  diagram_caption?: string;
  rank?: number;
  score?: number;
  rerank_score?: number;
  match_type?: string;
}

export type CardType = 'user' | 'normal' | 'ambiguity' | 'refusal';

export interface AmbiguityOption {
  machine: string;
  label: string;
  description: string;
  queryHint?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  cardType: CardType;
  timestamp: string;
  
  // User question
  content?: string;

  // Normal answer structure
  meaning?: string;
  causes?: string[];
  steps?: string[];
  citations?: Citation[];
  diagrams?: Diagram[];
  detectedMachine?: string;
  machineSource?: string;

  // Ambiguity clarification structure
  ambiguityPrompt?: string;
  ambiguityOptions?: AmbiguityOption[];

  // Refusal structure
  refusalMessage?: string;
}

export interface SessionMemoryState {
  sessionId: string;
  lastMachine: string | null;
  lastError: string | null;
  updatedAt?: string;
}

export interface EventTrailItem {
  id: string;
  timestamp: string;
  type: 'context_switch' | 'system' | 'query';
  machine?: string;
  text: string;
  shortcut?: string;
}

export interface BackendConfig {
  mode: 'demo' | 'live';
  baseUrl: string;
}
