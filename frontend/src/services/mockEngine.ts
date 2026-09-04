import type { Message, SessionMemoryState, Machine } from '../types';

export const INITIAL_MACHINES: Machine[] = [
  {
    id: 'CNC-100',
    name: 'CNC Machining Center (CNC-100)',
    category: 'CNC Machining Center',
    manualFile: 'cnc100.txt',
    indexed: true,
    pageCount: 4,
  },
  {
    id: 'Press-200',
    name: 'Hydraulic Press (Press-200)',
    category: 'Hydraulic Press',
    manualFile: 'press200.txt',
    indexed: true,
    pageCount: 4,
  },
  {
    id: 'RobotArm-300',
    name: 'Articulated Robot (RobotArm-300)',
    category: 'Articulated Robot',
    manualFile: 'robotarm300.txt',
    indexed: true,
    pageCount: 2,
  },
];

export function extractMachineAndError(query: string, currentSession: SessionMemoryState): { machine: string | null; error: string | null } {
  const q = query.toLowerCase();

  let machine = currentSession.lastMachine;
  if (q.includes('cnc-100') || q.includes('cnc100') || q.includes('cnc')) {
    machine = 'CNC-100';
  } else if (q.includes('press-200') || q.includes('press200') || q.includes('press')) {
    machine = 'Press-200';
  } else if (q.includes('robotarm-300') || q.includes('robotarm') || q.includes('robot')) {
    machine = 'RobotArm-300';
  }

  let error = currentSession.lastError;
  const match = query.match(/\b([EHR]\d{3}|SYM-[A-Z0-9-]+)\b/i);
  if (match) {
    error = match[1].toUpperCase();
  }

  return { machine, error };
}

export async function processMockQuery(
  userQuery: string,
  sessionState: SessionMemoryState,
  scopedMachine: string | null
): Promise<{ message: Message; newSession: SessionMemoryState }> {
  // Simulate industrial fast RAG processing latency (350-500ms)
  await new Promise((resolve) => setTimeout(resolve, 400));

  const trimmed = userQuery.trim();
  const lower = trimmed.toLowerCase();
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const msgId = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;

  let detectedMachine = scopedMachine || null;
  if (!detectedMachine) {
    if (lower.includes('cnc-100') || lower.includes('cnc100') || lower.includes('cnc')) {
      detectedMachine = 'CNC-100';
    } else if (lower.includes('press-200') || lower.includes('press200') || lower.includes('press')) {
      detectedMachine = 'Press-200';
    } else if (lower.includes('robotarm-300') || lower.includes('robotarm') || lower.includes('robot')) {
      detectedMachine = 'RobotArm-300';
    }
  }

  const errorMatch = trimmed.match(/\b([EHR]\d{3}|SYM-[A-Z0-9-]+)\b/i);
  const detectedError = errorMatch ? errorMatch[1].toUpperCase() : sessionState.lastError;

  // SCENARIO 4: Insufficient Information / Honest Refusal Check
  if (
    lower.includes('spindle bearing') ||
    lower.includes('replace spindle bearing') ||
    lower.includes('status led') ||
    lower.includes('flashing 3 short blinks') ||
    lower.includes('flickering pattern')
  ) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'refusal',
        timestamp,
        refusalMessage: "The manuals don't cover this. I won't guess at a fix.",
      },
      newSession: {
        ...sessionState,
        lastMachine: detectedMachine || sessionState.lastMachine,
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 3: Cross-Manual Ambiguity Check (E101 exists on CNC-100 and Press-200)
  const isAmbiguousQuery =
    (lower.includes('e101') && !detectedMachine) ||
    lower === 'what does e101 mean?' ||
    lower === 'what does error e101 mean?' ||
    lower === 'e101' ||
    lower === 'how do i fix error e101?' ||
    lower === 'how do i fix e101?';

  if (isAmbiguousQuery) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'ambiguity',
        timestamp,
        ambiguityPrompt: 'That error code exists on more than one machine. Which one are you asking about?',
        ambiguityOptions: [
          {
            machine: 'CNC-100',
            label: 'CNC-100 — Excessive motor temperature',
            description: 'Cooling fan failure or excessive spindle load on CNC-100 machining center',
            queryHint: 'What does E101 mean on CNC-100?',
          },
          {
            machine: 'Press-200',
            label: 'Press-200 — Hydraulic oil pressure low',
            description: 'Hydraulic fluid leak or faulty hydraulic pump valve on Press-200',
            queryHint: 'Why is Press-200 stopping due to oil pressure?',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastError: 'E101',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1A: Exact code on CNC-100 (E101)
  if ((detectedMachine === 'CNC-100' || lower.includes('cnc')) && (lower.includes('e101') || sessionState.lastError === 'E101')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Excessive motor temperature.',
        causes: [
          'Cooling fan failure',
          'Blocked ventilation',
          'Excessive spindle load',
        ],
        steps: [
          'Switch off the CNC-100 machine immediately.',
          'Inspect the rear cooling fan for debris.',
          'Clean all ventilation openings.',
          'Allow spindle motor to cool down for 20 minutes before restarting.',
        ],
        citations: [
          {
            manual: 'cnc100.txt',
            page: 2,
            section: 'E101 Troubleshooting',
            snippet: 'SECTION: E101 Troubleshooting\nPAGE: 2\nMACHINE: CNC-100\nMODEL: X200\nERROR CODE: E101\nSTEPS:\n1. Switch off the CNC-100 machine immediately.\n2. Inspect the rear cooling fan for debris.\n3. Clean all ventilation openings.\n4. Allow spindle motor to cool down for 20 minutes before restarting.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'CNC-100',
        lastError: 'E101',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1B: Exact code / symptom on Press-200 (E101 or oil pressure)
  if ((detectedMachine === 'Press-200' || lower.includes('press') || lower.includes('oil pressure')) && (lower.includes('e101') || lower.includes('oil pressure') || sessionState.lastError === 'E101')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Hydraulic oil pressure low.',
        causes: [
          'Hydraulic fluid leak',
          'Faulty hydraulic pump valve',
          'Worn pressure seals',
        ],
        steps: [
          'Shut down Press-200 hydraulic unit.',
          'Check hydraulic fluid level gauge on main tank.',
          'Inspect main pressure line hoses for visible leaks.',
          'Replace seals or top up ISO VG 46 hydraulic oil.',
        ],
        citations: [
          {
            manual: 'press200.txt',
            page: 2,
            section: 'E101 Troubleshooting',
            snippet: 'SECTION: E101 Troubleshooting\nPAGE: 2\nMACHINE: Press-200\nMODEL: P400\nERROR CODE: E101\nSTEPS:\n1. Shut down Press-200 hydraulic unit.\n2. Check hydraulic fluid level gauge on main tank.\n3. Inspect main pressure line hoses for visible leaks.\n4. Replace seals or top up ISO VG 46 hydraulic oil.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Press-200',
        lastError: 'E101',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1C: RobotArm-300 (R101)
  if ((detectedMachine === 'RobotArm-300' || lower.includes('robot') || lower.includes('arm')) && (lower.includes('r101') || sessionState.lastError === 'R101')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Joint rotational deviation.',
        causes: [
          'Harmonic drive wear',
          'Encoder pulse mismatch',
        ],
        steps: [
          'Brake the robotic arm joints.',
          'Inspect encoder connection cable.',
          'Perform home calibration cycle.',
        ],
        citations: [
          {
            manual: 'robotarm300.txt',
            page: 2,
            section: 'R101 Troubleshooting',
            snippet: 'SECTION: R101 Troubleshooting\nPAGE: 2\nMACHINE: RobotArm-300\nMODEL: R300\nERROR CODE: R101\nSTEPS:\n1. Brake the robotic arm joints.\n2. Inspect encoder connection cable.\n3. Perform home calibration cycle.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'RobotArm-300',
        lastError: 'R101',
        updatedAt: timestamp,
      },
    };
  }

  // Default fallback answer
  return {
    message: {
      id: msgId,
      role: 'assistant',
      cardType: 'normal',
      timestamp,
      meaning: `Diagnostic procedure evaluated for ${detectedMachine || 'plant equipment'}.`,
      causes: ['Operating condition outside standard parameters.'],
      steps: ['Consult equipment service manual and verify safety disconnect.'],
      citations: [
        {
          manual: detectedMachine === 'CNC-100' ? 'cnc100.txt' : (detectedMachine === 'Press-200' ? 'press200.txt' : 'robotarm300.txt'),
          page: 1,
          section: 'Equipment Overview',
          snippet: 'Manual-sourced technical documentation guidelines.',
        },
      ],
    },
    newSession: {
      ...sessionState,
      lastMachine: detectedMachine || sessionState.lastMachine,
      lastError: detectedError || sessionState.lastError,
      updatedAt: timestamp,
    },
  };
}
