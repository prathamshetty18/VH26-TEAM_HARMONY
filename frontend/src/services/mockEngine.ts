import type { Message, SessionMemoryState, Machine } from '../types';

export const INITIAL_MACHINES: Machine[] = [
  {
    id: 'CNC-100',
    name: 'CNC-100 Milling Center',
    category: '5-Axis CNC Mill',
    manualFile: 'cnc100.txt',
    indexed: true,
    pageCount: 148,
  },
  {
    id: 'Press-200',
    name: 'Press-200 Hydraulic Stamper',
    category: 'Hydraulic Forming Press',
    manualFile: 'press200.txt',
    indexed: true,
    pageCount: 92,
  },
  {
    id: 'RobotArm-300',
    name: 'RobotArm-300 Articulated Arm',
    category: '6-Axis Material Handler',
    manualFile: 'robotarm300.txt',
    indexed: true,
    pageCount: 116,
  },
];

export function extractMachineAndError(query: string, currentSession: SessionMemoryState): { machine: string | null; error: string | null } {
  const q = query.toUpperCase();

  let machine = currentSession.lastMachine;
  if (q.includes('CNC-100') || q.includes('CNC100') || q.includes('CNC')) {
    machine = 'CNC-100';
  } else if (q.includes('PRESS-200') || q.includes('PRESS200') || q.includes('PRESS')) {
    machine = 'Press-200';
  } else if (q.includes('ROBOTARM-300') || q.includes('ROBOTARM') || q.includes('ROBOT') || q.includes('ARM-300')) {
    machine = 'RobotArm-300';
  }

  let error = currentSession.lastError;
  const match = query.match(/\b([EAP]\d{3,4}|ERR[-_]?\d+)\b/i);
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
  // Simulate industrial fast RAG processing latency (350-600ms)
  await new Promise((resolve) => setTimeout(resolve, 450));

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

  const errorMatch = trimmed.match(/\b([EAP]\d{3,4}|ERR[-_]?\d+)\b/i);
  const detectedError = errorMatch ? errorMatch[1].toUpperCase() : sessionState.lastError;

  // SCENARIO 4: Insufficient Information / Refusal Check
  if (
    lower.includes('replace spindle bearing') ||
    lower.includes('rebuild gearbox') ||
    lower.includes('rewrite plc firmware') ||
    lower.includes('bypass safety light curtain')
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

  // SCENARIO 3: Cross-Manual Ambiguity Check
  const isAmbiguousQuery =
    (lower.includes('e101') && !detectedMachine) ||
    (lower === 'what does e101 mean?' || lower === 'e101' || lower === 'what does e101 mean');

  if (isAmbiguousQuery) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'ambiguity',
        timestamp,
        ambiguityPrompt: 'E101 means something different on each machine — which one are you asking about?',
        ambiguityOptions: [
          {
            machine: 'CNC-100',
            label: 'CNC-100 — Spindle motor overheating',
            description: 'Thermal overload trip on main 15kW spindle drive motor',
            queryHint: 'What does E101 mean on CNC-100?',
          },
          {
            machine: 'Press-200',
            label: 'Press-200 — Hydraulic manifold pressure fault',
            description: 'Proportional relief valve differential pressure cutoff',
            queryHint: 'What does E101 mean on Press-200?',
          },
          {
            machine: 'RobotArm-300',
            label: 'RobotArm-300 — Joint 1 axis communication fault',
            description: 'CANbus packet collision on primary waist rotation servo',
            queryHint: 'What does E101 mean on RobotArm-300?',
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

  // SCENARIO 1: Exact error code (e.g. "What does E101 mean on CNC-100?")
  if ((detectedMachine === 'CNC-100' && (lower.includes('e101') || sessionState.lastError === 'E101')) || (lower.includes('e101') && lower.includes('cnc-100'))) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'E101 indicates spindle drive motor thermal overload cutoff during high-torque cutting cycles.',
        causes: [
          'Coolant flow restricted or blocked to the spindle jacket heat exchanger.',
          'Thermal RTD sensor probe fouled with metal fines or disconnected at terminal TB3.',
          'Continuous duty cycle exceeded 85% rated load for over 45 minutes.',
        ],
        steps: [
          'Verify fluid manifold sight glass and accumulator pressure gauge.',
          'Cycle valve test sequence 4B from manual service override pendant.',
          'Perform filter cart flush cycle and log differential delta pressure.',
        ],
        citations: [
          {
            manual: 'cnc100.txt',
            page: 4,
            section: 'E101 Troubleshooting - Spindle Thermal Overload',
            snippet: 'Section 4.2 Spindle Thermal Cutoff (E101): Thermal sensor triggers safety shutoff when stator temperature exceeds 105°C. Check coolant lines and reset breaker after 15-minute cooldown.',
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

  // SCENARIO 2: Natural language symptom
  if (
    (detectedMachine === 'Press-200' && (lower.includes('oil pressure') || lower.includes('hydraulic') || lower.includes('stopping') || lower.includes('pressure'))) ||
    lower.includes('oil pressure') ||
    lower.includes('stopping due to oil pressure')
  ) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Press-200 emergency stop triggered by hydraulic low-pressure interlock before ram stroke completion.',
        causes: [
          'Hydraulic return line filter element clogged (differential bypass threshold exceeded).',
          'Main variable-displacement pump cavitation caused by low ISO VG 46 reservoir level.',
          'Proportional pressure relief valve PRV-1 spool sticking in open bypass position.',
        ],
        steps: [
          'Inspect reservoir sight level gauge at rear service access hatch.',
          'Check differential pressure indicator on main high-pressure filter bowl (red flag visible = bypass active).',
          'Verify proportional relief valve coil resistance across pins A and B (spec: 18.5 - 22.0 Ω).',
        ],
        citations: [
          {
            manual: 'press200.txt',
            page: 12,
            section: 'Hydraulic Interlock & Pressure Loss',
            snippet: 'Section 6.1 Low Hydraulic Head: If pressure drops below 160 bar during ram advance, safety interlock dumps pilot pressure. Inspect primary filter element P/N HY-2201 and oil reservoir level.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Press-200',
        lastError: 'OIL_PRESS_FAULT',
        updatedAt: timestamp,
      },
    };
  }

  // Fallback for RobotArm-300
  if (detectedMachine === 'RobotArm-300' || lower.includes('robotarm') || lower.includes('a032')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'A032 indicates absolute optical encoder communication timeout on Joint 3 (Elbow pitch).',
        causes: [
          'Internal flex cable harness wear at articulation point J2/J3.',
          'Transient 24V DC logic supply dip below 20.4V during rapid arm deceleration.',
          'Optical disk contaminated by vaporized grease seal leak.',
        ],
        steps: [
          'Power down arm controller and inspect harness conduit bracket J2-B for cable pinching.',
          'Measure regulated 24V supply rail on rack terminal block X2 during brake release cycle.',
          'Perform manual zero-calibration offset check using calibration pin P-300.',
        ],
        citations: [
          {
            manual: 'robotarm300.txt',
            page: 38,
            section: 'A032 Encoder Data Bus Timeout',
            snippet: 'Section 9.4 Joint Encoder Bus: When serial frame drops exceed 3 consecutive cycles, axis driver halts motion immediately to prevent runaway kinematic divergence.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'RobotArm-300',
        lastError: 'A032',
        updatedAt: timestamp,
      },
    };
  }

  if (lower.length < 5) {
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

  const activeMach = detectedMachine || 'CNC-100';
  const manualName = activeMach === 'CNC-100' ? 'cnc100.txt' : activeMach === 'Press-200' ? 'press200.txt' : 'robotarm300.txt';
  const pageNum = activeMach === 'CNC-100' ? 8 : activeMach === 'Press-200' ? 19 : 24;

  return {
    message: {
      id: msgId,
      role: 'assistant',
      cardType: 'normal',
      timestamp,
      meaning: `Diagnostic response for ${activeMach} based on technical manual specifications.`,
      causes: [
        'Intermittent sensor drift during steady-state production run.',
        'Mechanical tolerance deviation outside ±0.05mm calibrated envelope.',
      ],
      steps: [
        'Isolate machine main power switch and tag out according to shop procedure.',
        `Inspect wiring harness connectors as referenced in ${manualName} Section 3.`,
        'Execute diagnostic self-test from control cabinet diagnostic screen.',
      ],
      citations: [
        {
          manual: manualName,
          page: pageNum,
          section: `${activeMach} Diagnostic Specifications`,
          snippet: `Section 3.1 Maintenance protocols for ${activeMach}. Perform daily inspections and verify zero calibration prior to production shifts.`,
        },
      ],
    },
    newSession: {
      ...sessionState,
      lastMachine: activeMach,
      lastError: detectedError || 'DIAG_CHECK',
      updatedAt: timestamp,
    },
  };
}
