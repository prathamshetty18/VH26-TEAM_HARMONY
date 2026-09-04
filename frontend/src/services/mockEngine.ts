import type { Message, SessionMemoryState, Machine } from '../types';

export const INITIAL_MACHINES: Machine[] = [
  {
    id: 'Conveyor Belt System',
    name: 'Conveyor Belt System (CB-4400)',
    category: 'Material Handling Conveyor',
    manualFile: 'conveyorcb4400.txt',
    indexed: true,
    pageCount: 6,
  },
  {
    id: 'CNC Milling Machine',
    name: 'CNC Milling Machine (MX-7 Precision)',
    category: '5-Axis Vertical Machining',
    manualFile: 'cncmx7.txt',
    indexed: true,
    pageCount: 6,
  },
  {
    id: 'Hydraulic Press',
    name: 'Hydraulic Press (HP-2200)',
    category: 'Hydraulic Forming Press',
    manualFile: 'presshp2200.txt',
    indexed: true,
    pageCount: 6,
  },
];

export function extractMachineAndError(query: string, currentSession: SessionMemoryState): { machine: string | null; error: string | null } {
  const q = query.toLowerCase();

  let machine = currentSession.lastMachine;
  if (q.includes('cb-4400') || q.includes('cb4400') || q.includes('conveyor')) {
    machine = 'Conveyor Belt System';
  } else if (q.includes('mx-7') || q.includes('mx7') || q.includes('cnc') || q.includes('milling')) {
    machine = 'CNC Milling Machine';
  } else if (q.includes('hp-2200') || q.includes('hp2200') || q.includes('hydraulic') || q.includes('press')) {
    machine = 'Hydraulic Press';
  }

  let error = currentSession.lastError;
  const match = query.match(/\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b/i);
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
    if (lower.includes('cb-4400') || lower.includes('cb4400') || lower.includes('conveyor')) {
      detectedMachine = 'Conveyor Belt System';
    } else if (lower.includes('mx-7') || lower.includes('mx7') || lower.includes('cnc') || lower.includes('milling')) {
      detectedMachine = 'CNC Milling Machine';
    } else if (lower.includes('hp-2200') || lower.includes('hp2200') || lower.includes('hydraulic') || lower.includes('press')) {
      detectedMachine = 'Hydraulic Press';
    }
  }

  const errorMatch = trimmed.match(/\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b/i);
  const detectedError = errorMatch ? errorMatch[1].toUpperCase() : sessionState.lastError;

  // SCENARIO 4: Insufficient Information / Honest Refusal Check
  if (
    lower.includes('status led') ||
    lower.includes('flashing 3 short blinks') ||
    lower.includes('flickering pattern') ||
    lower.includes('led is blinking') ||
    lower.includes('led pattern') ||
    lower.includes('blink pattern')
  ) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'refusal',
        timestamp,
        refusalMessage: "The available manuals do not provide sufficient information to answer this. I won't provide an unsupported answer.",
      },
      newSession: {
        ...sessionState,
        lastMachine: detectedMachine || sessionState.lastMachine,
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 3: Cross-Manual Ambiguity Check (E101 exists on Conveyor CB-4400 and CNC MX-7)
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
        ambiguityPrompt: 'Multiple machines match this error code. Please select which machine you are operating:',
        ambiguityOptions: [
          {
            machine: 'Conveyor Belt System (CB-4400)',
            label: 'Conveyor Belt System (CB-4400) — VFD drive motor phase overcurrent fault',
            description: 'VFD inverter detects motor phase current draw exceeding 125% FLA for >3.5s',
            queryHint: 'How do I fix error E101 on the CB-4400 conveyor belt?',
          },
          {
            machine: 'CNC Milling Machine (MX-7 Precision)',
            label: 'CNC Milling Machine (MX-7 Precision) — Spindle coolant flow failure (<3.8 L/min via FL-10)',
            description: 'Through-spindle coolant flow falling below 3.8 L/min threshold during active spindle rotation',
            queryHint: 'What does error E101 mean on the CNC Milling Machine MX-7 Precision?',
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

  // SCENARIO 1A: Exact code on Conveyor Belt (E101)
  if ((detectedMachine === 'Conveyor Belt System' || lower.includes('conveyor') || lower.includes('cb-4400')) && (lower.includes('e101') || sessionState.lastError === 'E101')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'E101 on the Conveyor Belt System (CB-4400) indicates a Drive Motor Overcurrent Fault. The VFD inverter detects motor phase current exceeding 125% of FLA for >3.5s.',
        causes: [
          'Excessive conveyor belt tension creating abnormal mechanical resistance on the head drive drum.',
          'Mechanical seizure or bearing galling in carrying or return idler rollers.',
          'Foreign debris or broken packaging wedged between slider bed and belt underside.',
        ],
        steps: [
          'Lock out and tag out (LOTO) the main electrical disconnect switch at control panel CP-1.',
          'Inspect carrying deck and return run for jammed pallets, packaging, or foreign debris.',
          'Loosen dual take-up jack screws on tail pulley and verify belt deflection tension (25 mm under 15 kg test point).',
          'Rotate drive drum and snub rollers by hand to verify free rotation; replace stiff idler rollers.',
          'Verify VFD parameter P-042 matches motor nameplate amperage.',
          'Remove LOTO, reset VFD fault keypad, and perform 5-minute unloaded test run monitoring line current.',
        ],
        citations: [
          {
            manual: 'conveyorcb4400.txt',
            page: 2,
            section: 'E101 — Drive Motor Overcurrent Fault',
            snippet: 'Conveyor Belt System Model CB-4400 Section 2: E101 Drive Motor Overcurrent Fault. LOTO main disconnect switch at control panel CP-1. Deflection tension spec: 25 mm under 15 kg test point.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Conveyor Belt System',
        lastError: 'E101',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1B: Exact code on CNC MX-7 (E101)
  if ((detectedMachine === 'CNC Milling Machine' || lower.includes('cnc') || lower.includes('mx-7') || lower.includes('milling')) && (lower.includes('e101') || sessionState.lastError === 'E101')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'E101 on the CNC Milling Machine Model MX-7 Precision indicates a Spindle Coolant Flow Failure. Inline flow sensor FL-10 measures coolant delivery below 3.8 L/min while spindle exceeds 1,000 RPM.',
        causes: [
          'Clogged 25-micron inline high-pressure coolant filter cartridge (MX-FLT-025).',
          'Coolant supply pump cavitation or low fluid level in the 300-liter reservoir.',
          'Severed, crushed, or twisted high-pressure braided coolant delivery hose in the Z-axis drag chain.',
        ],
        steps: [
          'Abort active program and ensure cutting zone coolant spray has settled.',
          'Check rear filtration tank level sight gauge and top up with 8% water-soluble synthetic emulsion.',
          'Inspect differential pressure indicator; replace 25-micron pleated cartridge (Part No. MX-FLT-025).',
          'Inspect braided delivery lines running through Z-axis energy chain for crushing or kinks.',
          'Verify high-pressure coolant pump gauge reads 45-70 bar during M08 activation.',
          'In MDI mode, command M08; and confirm digital flow rate display exceeds 6.2 L/min.',
        ],
        citations: [
          {
            manual: 'cncmx7.txt',
            page: 2,
            section: 'E101 — Spindle Coolant Flow Failure',
            snippet: 'CNC Milling Machine Model MX-7 Precision Section 2: E101 Spindle Coolant Flow Failure. Flow sensor FL-10 threshold: 3.8 L/min. Replace 25-micron filter cartridge Part No. MX-FLT-025.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'CNC Milling Machine',
        lastError: 'E101',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1C: Exact code on Hydraulic Press (H205)
  if ((detectedMachine === 'Hydraulic Press' || lower.includes('press') || lower.includes('hp-2200')) && (lower.includes('h205') || sessionState.lastError === 'H205')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'H205 on the HP-2200 Hydraulic Press indicates Hydraulic Oil High Temperature. Sump thermistor TT-02 detects oil temperature exceeding 65°C.',
        causes: [
          'Clogged duplex heat exchanger basket strainer restricting cooling water flow.',
          'Cooling water supply pressure below required 3.5 bar threshold.',
          'Main relief valve internal bypass leaking pressurized fluid directly to tank.',
        ],
        steps: [
          'Allow main pump to idle unloaded for 10 minutes to circulate fluid through heat exchanger.',
          'Clean duplex basket strainer elements in mineral spirits and flush housing.',
          'Verify incoming factory cooling water supply pressure reads at least 3.5 bar.',
          'Inspect thermostatic water regulating valve TCV-12 for proper stroke travel.',
        ],
        citations: [
          {
            manual: 'presshp2200.txt',
            page: 2,
            section: 'H205 Troubleshooting',
            snippet: 'Hydraulic Press Model HP-2200 Section 2: H205 Hydraulic Oil High Temperature. Sensor TT-02 alarm threshold: 65°C. Verify cooling water pressure >= 3.5 bar.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Hydraulic Press',
        lastError: 'H205',
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 2A: Symptom - Conveyor Squealing
  if (lower.includes('squeal') || lower.includes('chirp') || lower.includes('startup')) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Squealing and chirping during morning startup on the CB-4400 indicates Drive Drum Lagging Glazing or initial belt slippage under acceleration inertia.',
        causes: [
          'Glazed or worn rubber lagging on primary drive drum.',
          'Insufficient belt tension allowing drum to slip during motor startup torque ramp.',
          'Stiff, dry pillow block bearings in the adjacent snub roller.',
        ],
        steps: [
          'Tighten left and right tail pulley take-up bolts equally by 2 full turns to eliminate startup slippage.',
          'Inspect drive drum rubber lagging; scuff glazed surface with 40-grit emery cloth to restore traction.',
          'Apply conveyor belt grip conditioning spray if ambient humidity is elevated.',
          'Lubricate snub roller pillow block bearings with 2 pumps of NLGI Grade 2 lithium grease.',
        ],
        citations: [
          {
            manual: 'conveyorcb4400.txt',
            page: 5,
            section: 'Startup Squeal Troubleshooting',
            snippet: 'Conveyor Belt System CB-4400 Section 3: Squealing or Chirping Sound During Startup. Tighten tail pulley take-up screws 2 full turns; scuff lagging with 40-grit emery cloth.',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Conveyor Belt System',
        lastError: 'SYM-SQUEAL-STARTUP',
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
          manual: detectedMachine === 'CNC Milling Machine' ? 'cncmx7.txt' : (detectedMachine === 'Hydraulic Press' ? 'presshp2200.txt' : 'conveyorcb4400.txt'),
          page: 1,
          section: 'Equipment Overview',
          snippet: 'Manufacturer standard operating guidelines.',
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
