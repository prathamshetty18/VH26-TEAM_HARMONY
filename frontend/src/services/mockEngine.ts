import type { Message, SessionMemoryState, Machine } from '../types';

export const INITIAL_MACHINES: Machine[] = [
  {
    id: 'Hydraulic Press',
    name: 'Hydraulic Press (HP-2200)',
    category: 'Hydraulic Press',
    manualFile: 'presshp2200.txt',
    indexed: true,
    pageCount: 6,
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
    id: 'CNC-100',
    name: 'CNC Machining Center (CNC-100)',
    category: 'CNC Machining Center',
    manualFile: 'cnc100.txt',
    indexed: true,
    pageCount: 4,
  },
  {
    id: 'CNC Milling Machine',
    name: 'CNC Milling Machine (MX-7)',
    category: 'CNC Milling Machine',
    manualFile: 'cncmx7.txt',
    indexed: true,
    pageCount: 6,
  },
  {
    id: 'Conveyor Belt System',
    name: 'Conveyor Belt System (CB-4400)',
    category: 'Material Handling',
    manualFile: 'conveyorcb4400.txt',
    indexed: true,
    pageCount: 6,
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
  if (q.includes('hp-2200') || q.includes('hp2200') || q.includes('hydraulic press') || q.includes('hp press')) {
    machine = 'Hydraulic Press';
  } else if (q.includes('press-200') || q.includes('press200') || q.includes('press')) {
    machine = 'Press-200';
  } else if (q.includes('cnc-100') || q.includes('cnc100') || q.includes('cnc')) {
    machine = 'CNC-100';
  } else if (q.includes('mx-7') || q.includes('mx7') || q.includes('milling')) {
    machine = 'CNC Milling Machine';
  } else if (q.includes('cb-4400') || q.includes('cb4400') || q.includes('conveyor')) {
    machine = 'Conveyor Belt System';
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
    if (lower.includes('hp-2200') || lower.includes('hp2200') || lower.includes('hydraulic press') || lower.includes('hp press')) {
      detectedMachine = 'Hydraulic Press';
    } else if (lower.includes('press-200') || lower.includes('press200') || lower.includes('press')) {
      detectedMachine = 'Press-200';
    } else if (lower.includes('cnc-100') || lower.includes('cnc100') || lower.includes('cnc')) {
      detectedMachine = 'CNC-100';
    } else if (lower.includes('mx-7') || lower.includes('mx7') || lower.includes('milling')) {
      detectedMachine = 'CNC Milling Machine';
    } else if (lower.includes('cb-4400') || lower.includes('cb4400') || lower.includes('conveyor')) {
      detectedMachine = 'Conveyor Belt System';
    } else if (lower.includes('robotarm-300') || lower.includes('robotarm') || lower.includes('robot')) {
      detectedMachine = 'RobotArm-300';
    }
  }



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

  // SCENARIO 1A: Exact code or diagram on CNC-100 (E101 / diagram)
  if ((detectedMachine === 'CNC-100' || lower.includes('cnc-100') || lower.includes('cnc 100')) && (lower.includes('e101') || lower.includes('diagram') || lower.includes('schematic') || lower.includes('image') || sessionState.lastError === 'E101')) {
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
            diagram_url: '/diagrams/cnc100_cooling_fan.svg',
            diagram_title: 'Cooling Circuit & Spindle Thermal Flow Diagram',
            diagram_caption: 'Rear cooling fan assembly, ventilation ducts, and heat dissipation path',
          },
        ],
        diagrams: [
          {
            title: 'Cooling Circuit & Spindle Thermal Flow Diagram',
            filename: 'cnc100_cooling_fan.svg',
            url: '/diagrams/cnc100_cooling_fan.svg',
            caption: 'Rear cooling fan assembly, ventilation ducts, and heat dissipation path',
            system: 'CNC-100',
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

  // SCENARIO 1B: Exact code / symptom / diagram on Press-200 (E101 or oil pressure or diagram)
  if ((detectedMachine === 'Press-200' || lower.includes('press-200') || lower.includes('press 200')) && (lower.includes('e101') || lower.includes('e202') || lower.includes('e203') || lower.includes('oil pressure') || lower.includes('diagram') || lower.includes('schematic') || lower.includes('image') || sessionState.lastError === 'E101')) {
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
            diagram_url: '/diagrams/press200_hydraulic_circuit.svg',
            diagram_title: 'Main Cylinder Hydraulic Pressure Loop',
            diagram_caption: 'Pump intake manifold, relief bypass valve, and main ram chamber',
          },
        ],
        diagrams: [
          {
            title: 'Main Cylinder Hydraulic Pressure Loop',
            filename: 'press200_hydraulic_circuit.svg',
            url: '/diagrams/press200_hydraulic_circuit.svg',
            caption: 'Pump intake manifold, relief bypass valve, and main ram chamber',
            system: 'Press-200',
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

  // SCENARIO 1D: Hydraulic Press (HP-2200 / H201 / H205 / H312 / General Diagram)
  if (
    detectedMachine === 'Hydraulic Press' ||
    lower.includes('hp-2200') ||
    lower.includes('hp2200') ||
    lower.includes('hydraulic press') ||
    lower.includes('h201') ||
    lower.includes('h205') ||
    lower.includes('h312') ||
    (detectedMachine === 'Hydraulic Press' && (lower.includes('diagram') || lower.includes('schematic') || lower.includes('image')))
  ) {
    const isH205 = lower.includes('h205');
    const isH312 = lower.includes('h312');
    const isDiagOnly = lower.includes('diagram') || lower.includes('schematic');

    const errCode = isH205 ? 'H205' : (isH312 ? 'H312' : 'H201');
    const meaning = isH205
      ? 'Hydraulic Oil High Temperature Shutdown.'
      : (isH312
        ? 'Accumulator Precharge Pressure Below Threshold.'
        : (isDiagOnly
          ? 'Main Ram Proportional Hydraulic Manifold & Pressure Loop.'
          : 'Main Ram Proportional Pressure Loss.'));
    const causes = isH205
      ? ['Heat exchanger water flow blocked', 'Thermostatic valve stuck closed', 'Prolonged high pressure relief bypass']
      : ['Proportional valve PV-01 sticking or spool contamination', 'Pressure transducer PT-01 calibration drift', 'Pilot check valve seal degradation'];
    const steps = isH205
      ? ['Check water chiller supply line', 'Inspect oil cooler heat exchanger core', 'Verify thermostatic valve modulates at 50 deg C']
      : ['Refer to the technical manifold schematic below', 'Verify PT-01 transducer signal with multimeter (4-20mA)', 'Inspect proportional valve PV-01 spool for contamination', 'Perform hydraulic pressure recalibration'];

    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning,
        causes,
        steps,
        citations: [
          {
            manual: 'presshp2200.txt',
            page: 2,
            section: `${errCode} Troubleshooting`,
            snippet: `SECTION: ${errCode} Troubleshooting\nPAGE: 2\nMACHINE: Hydraulic Press\nMODEL: HP-2200\nERROR CODE: ${errCode}\nSTEPS:\n1. Refer to technical manifold schematic.\n2. Inspect proportional directional valve PV-01.\n3. Verify hydraulic pressure lines.`,
            diagram_url: '/diagrams/hydraulic_press_manifold.svg',
            diagram_title: 'Main Ram Proportional Hydraulic Manifold',
            diagram_caption: 'Proportional directional valve PV-01, cylinder pressure transducer PT-01, and pilot check line',
          },
        ],
        diagrams: [
          {
            title: 'Main Ram Proportional Hydraulic Manifold',
            filename: 'hydraulic_press_manifold.svg',
            url: '/diagrams/hydraulic_press_manifold.svg',
            caption: 'Proportional directional valve PV-01, cylinder pressure transducer PT-01, and pilot check line',
            system: 'Hydraulic Press',
          },
        ],
      },
      newSession: {
        ...sessionState,
        lastMachine: 'Hydraulic Press',
        lastError: errCode,
        updatedAt: timestamp,
      },
    };
  }

  // SCENARIO 1C: RobotArm-300 (R101 / General Robotics)
  if (
    detectedMachine === 'RobotArm-300' ||
    lower.includes('robot') ||
    lower.includes('arm') ||
    lower.includes('r101') ||
    lower.includes('r300') ||
    sessionState.lastMachine === 'RobotArm-300'
  ) {
    return {
      message: {
        id: msgId,
        role: 'assistant',
        cardType: 'normal',
        timestamp,
        meaning: 'Joint rotational deviation or axis servo tracking fault.',
        causes: [
          'Harmonic drive wear',
          'Encoder pulse mismatch',
          'Umbilical cable loose connection',
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
            diagram_url: '/diagrams/robot_arm_joint_drive.svg',
            diagram_title: 'Joint Axis Servo Drive & Dual Optical Encoder Loop',
            diagram_caption: 'AC synchronous brushless servo motor, harmonic drive reducer, and resolver feedback',
          },
        ],
        diagrams: [
          {
            title: 'Joint Axis Servo Drive & Dual Optical Encoder Loop',
            filename: 'robot_arm_joint_drive.svg',
            url: '/diagrams/robot_arm_joint_drive.svg',
            caption: 'AC synchronous brushless servo motor, harmonic drive reducer, and resolver feedback',
            system: 'RobotArm-300',
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

  // Default refusal for unsupported queries, foreign machines, unindexed codes, gibberish, or off-topic queries
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
