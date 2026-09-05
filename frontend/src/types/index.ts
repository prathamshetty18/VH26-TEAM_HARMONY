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

export interface PossibleFault {
  fault: string;
  fault_code?: string;
  fault_name?: string;
  confidence_score: number;
  confidence_percentage: number;
  confidence_level: string;
  is_primary: boolean;
  component?: string;
  supporting_evidence?: string[];
}

export interface FaultEvidence {
  contributing_evidence: string;
  reasoning: string;
  sensor_readings: Record<string, any>;
  reasoning_points?: string[];
  disclaimer: string;
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

  // Confidence scoring additions
  fault?: string;
  component?: string;
  confidence_score?: number;
  confidence_level?: string;
  confidence_percentage?: number;
  cause?: string;
  recommendation?: string;
  possible_faults?: PossibleFault[];
  evidence?: FaultEvidence;
  disclaimer?: string;

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
  voiceEnabled?: boolean;
}

export type VoiceState = 'ready' | 'listening' | 'processing' | 'complete' | 'error';

export interface VoiceTranscriptionResult {
  transcription: string;
  detectedLanguage: string;
  languageName: string;
  englishText: string;
  isTranslated: boolean;
  confidence?: number;
  error?: string;
}

export interface VoiceSample {
  id: string;
  language: string;
  language_name: string;
  sample_text: string;
  english_text: string;
  machine?: string;
  is_translated: boolean;
  description: string;
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
  is_translated?: boolean;
  source_language?: string | null;
  detected_language?: string | null;
}

