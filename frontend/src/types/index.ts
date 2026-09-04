export interface Machine {
  id: string;
  name: string;
  category: string;
  manualFile: string;
  indexed: boolean;
  pageCount: number;
}

export interface Citation {
  manual: string; // e.g. cnc100.txt
  page: number;   // e.g. 4
  section?: string; // e.g. E101 Troubleshooting - Spindle Overheat
  snippet?: string;
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

export interface ManualItem {
  filename: string;
  title: string;
  machine: string;
  pages: number;
  chunkCount: number;
  pdf_filename?: string | null;
  raw_text?: string;
  has_pdf?: boolean;
  pdf_url?: string | null;
}
