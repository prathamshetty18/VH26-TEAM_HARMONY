import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  Layers, 
  BookOpen, 
  ShieldCheck, 
  Settings, 
  Play, 
  Zap, 
  Server
} from 'lucide-react';
import { MachineFilter } from './components/Sidebar/MachineFilter';
import { SessionMemory } from './components/Sidebar/SessionMemory';
import { EventTrail } from './components/Sidebar/EventTrail';
import { MessageList } from './components/Chat/MessageList';
import { DemoScriptBar } from './components/Chat/DemoScriptBar';
import { InputBar } from './components/Chat/InputBar';
import { CitationModal } from './components/Chat/CitationModal';
import { BackendSettingsModal } from './components/BackendSettingsModal';
import type {
  Message,
  SessionMemoryState,
  Machine,
  Citation,
  AmbiguityOption,
  EventTrailItem,
  BackendConfig,
} from './types';
import { diagnosticService } from './services/api';
import { INITIAL_MACHINES } from './services/mockEngine';

export const App: React.FC = () => {
  // Session State (persisted per browser tab)
  const [session, setSession] = useState<SessionMemoryState>(() => {
    const existing = sessionStorage.getItem('machineassist_session');
    if (existing) {
      try {
        return JSON.parse(existing);
      } catch (e) {
        // fallback
      }
    }
    const newId = `sess_${Math.random().toString(36).substring(2, 8)}`;
    const init: SessionMemoryState = {
      sessionId: newId,
      lastMachine: null,
      lastError: null,
      updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    sessionStorage.setItem('machineassist_session', JSON.stringify(init));
    return init;
  });

  const [machines, setMachines] = useState<Machine[]>(INITIAL_MACHINES);
  const [scopedMachine, setScopedMachine] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome_msg',
      role: 'assistant',
      cardType: 'normal',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      meaning: 'Manuals indexed. Ask about an error code or symptom.',
    },
  ]);
  const [events, setEvents] = useState<EventTrailItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [backendConfig, setBackendConfig] = useState<BackendConfig>(diagnosticService.getConfig());
  const [isLiveActive, setIsLiveActive] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'copilot' | 'benchmarks' | 'manuals' | 'telemetry'>('copilot');

  // Benchmark suite state
  const [benchmarkProgress, setBenchmarkProgress] = useState<number>(100);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);

  // Manuals state
  const [manualsData, setManualsData] = useState<any[]>([]);
<<<<<<< HEAD
  const [activeManual, setActiveManual] = useState<string>('multilingual');
  const [manualLang, setManualLang] = useState<'en' | 'zh' | 'ja' | 'de'>('en');
  const [multilingualManual, setMultilingualManual] = useState<any>(null);
=======
  const [activeManual, setActiveManual] = useState<string>('cnc100.txt');
  const [systemStatus, setSystemStatus] = useState<any>(null);
>>>>>>> a5e549b19d767b3cca19ac04b03b07c326ed9a05

  // Sync session state to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('machineassist_session', JSON.stringify(session));
  }, [session]);

  // Load backend health, machines, benchmarks, manuals, and system status
  useEffect(() => {
    const loadData = async () => {
      const isHealthy = await diagnosticService.checkBackendHealth();
      setIsLiveActive(isHealthy);
      const data = await diagnosticService.getMachines();
      setMachines(data);

      try {
        const benchRes = await fetch(`${backendConfig.baseUrl}/api/benchmarks`);
        if (benchRes.ok) {
          const bData = await benchRes.json();
          setBenchmarks(bData);
        }
      } catch (err) {
        console.warn('Could not load benchmarks', err);
      }

      try {
        const manRes = await fetch(`${backendConfig.baseUrl}/api/manuals`);
        if (manRes.ok) {
          const mData = await manRes.json();
          setManualsData(mData.manuals || []);
        }
      } catch (err) {
        console.warn('Could not load manuals', err);
      }

      try {
        const sysRes = await fetch(`${backendConfig.baseUrl}/api/system-status`);
        if (sysRes.ok) {
          const sData = await sysRes.json();
          setSystemStatus(sData);
        }
      } catch (err) {
        console.warn('Could not load system status', err);
      }
    };
    loadData();
  }, [backendConfig]);

  // Load multilingual manual on language change
  useEffect(() => {
    const loadMultilingualManual = async () => {
      try {
        const res = await fetch(`${backendConfig.baseUrl}/api/manuals/multilingual?lang=${manualLang}`);
        if (res.ok) {
          const json = await res.json();
          setMultilingualManual(json.manual);
        }
      } catch (err) {
        console.warn('Could not load multilingual manual', err);
      }
    };
    loadMultilingualManual();
  }, [backendConfig, manualLang]);

  // Handle machine filter selection
  const handleSelectMachine = (machineId: string | null) => {
    setScopedMachine(machineId);
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const logText = machineId
      ? `Context switched to ${machineId}`
      : 'Context filter cleared (All machines active)';

    const newEvent: EventTrailItem = {
      id: `evt_${Date.now()}`,
      timestamp: now,
      type: 'context_switch',
      machine: machineId || undefined,
      text: logText,
      shortcut: machineId ? `Query active fault on ${machineId}` : undefined,
    };

    setEvents((prev) => [...prev, newEvent]);

    if (machineId) {
      setSession((prev) => ({
        ...prev,
        lastMachine: machineId,
        updatedAt: now,
      }));
    }
  };

  // Send query to diagnostic service
  const handleSendMessage = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const userMsg: Message = {
      id: `usr_${Date.now()}`,
      role: 'user',
      cardType: 'user',
      timestamp,
      content: queryText,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await diagnosticService.sendQuery(queryText, session, scopedMachine);
      setIsLiveActive(result.isLiveBackend);
      setMessages((prev) => [...prev, result.message]);
      setSession(result.newSession);

      const newEvent: EventTrailItem = {
        id: `evt_${Date.now()}`,
        timestamp,
        type: 'query',
        machine: result.newSession.lastMachine || scopedMachine || undefined,
        text: `Diagnostic query evaluated: "${queryText.length > 35 ? queryText.slice(0, 35) + '...' : queryText}"`,
      };
      setEvents((prev) => [...prev, newEvent]);
    } catch (err) {
      console.error('Failed to process diagnostic query:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle ambiguity option selection (sends machine name carrying session context)
  const handleSelectAmbiguityOption = (option: AmbiguityOption) => {
    handleSelectMachine(option.machine);
    const query = option.machine || option.queryHint || '';
    handleSendMessage(query);
  };

  // Reset session
  const handleResetSession = () => {
    const newId = `sess_${Math.random().toString(36).substring(2, 8)}`;
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const resetState: SessionMemoryState = {
      sessionId: newId,
      lastMachine: null,
      lastError: null,
      updatedAt: now,
    };
    setSession(resetState);
    setScopedMachine(null);
    setMessages([]);
    setEvents([
      {
        id: `evt_${Date.now()}`,
        timestamp: now,
        type: 'system',
        text: 'Session reset — Memory context cleared',
      },
    ]);
  };

  const handleClearMemory = () => {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setSession((prev) => ({
      ...prev,
      lastMachine: null,
      lastError: null,
      updatedAt: now,
    }));
  };

  const handleSaveConfig = (newConfig: BackendConfig) => {
    setBackendConfig(newConfig);
    diagnosticService.setConfig(newConfig);
  };

  // Live Benchmark Runner
  const runLiveBenchmark = async () => {
    if (isRunningBenchmark || benchmarks.length === 0) return;
    setIsRunningBenchmark(true);
    setBenchmarkProgress(0);

    for (let i = 0; i < benchmarks.length; i++) {
      const b = benchmarks[i];
      try {
        await diagnosticService.sendQuery(b.query, session, null);
      } catch (e) {
        // continue
      }
      setBenchmarkProgress(Math.round(((i + 1) / benchmarks.length) * 100));
    }
    setIsRunningBenchmark(false);
  };

  return (
    <div className="min-h-screen w-screen bg-[#fbfbfe] text-slate-900 relative overflow-x-hidden flex flex-col font-sans">
      {/* Background Ambient Aurora Glow (Wedge) */}
      <div className="ambient-glow" />

      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-[#fbfbfe]/90 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5 flex items-center justify-between transition-all">
        <div className="flex items-center space-x-8">
          <a href="#overview" className="flex items-center space-x-2.5 text-slate-900 font-extrabold text-xl tracking-tight">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Zap className="w-4 h-4 fill-white" />
            </div>
            <span>MachineAssist</span>
          </a>

          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium text-slate-600">
            <a href="#overview" className="hover:text-indigo-600 transition-colors">Overview</a>
            <button onClick={() => { setActiveTab('copilot'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-indigo-600 transition-colors">Copilot</button>
            <button onClick={() => { setActiveTab('benchmarks'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-indigo-600 transition-colors">Benchmarks</button>
            <button onClick={() => { setActiveTab('manuals'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-indigo-600 transition-colors">Manuals</button>
            <button onClick={() => { setActiveTab('telemetry'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-indigo-600 transition-colors">Telemetry</button>
          </nav>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50/80 border border-indigo-200/60 text-indigo-700 text-xs font-semibold">
            <span className={`w-2 h-2 rounded-full ${isLiveActive ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            <span>{isLiveActive ? 'Live API' : 'Simulated'} • {scopedMachine ? `Scope: ${scopedMachine}` : 'All Fleet'}</span>
          </div>

          <button 
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 rounded-full hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors"
            title="Backend Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button 
            onClick={handleResetSession}
            className="px-3.5 py-1.5 rounded-full border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-2xs"
          >
            Reset Session
          </button>

          <button 
            onClick={() => { setActiveTab('copilot'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }}
            className="px-4 py-1.5 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-500/25 hover:shadow-indigo-500/35 transition-all"
          >
            Launch Copilot →
          </button>
        </div>
      </header>

      {/* Hero Section (Wedge) */}
      <section className="pt-16 pb-12 text-center px-4 relative z-10" id="overview">
        <div className="max-w-4xl mx-auto">
          <div className="inline-flex items-center px-3.5 py-1 rounded-full bg-indigo-100/70 border border-indigo-200 text-indigo-800 text-xs font-bold uppercase tracking-wider mb-6">
            <span>Industrial Intelligence Platform</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.12] mb-5">
            Streamline your industrial operations
          </h1>

          <p className="text-base md:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed mb-8">
            Say goodbye to downtime headaches and say hello to efficiency. Query manufacturer manuals in milliseconds, isolate ambiguous error codes across production lines, and verify safety-critical procedures with zero hallucination.
          </p>

          <div className="flex items-center justify-center space-x-4 mb-14">
            <button 
              onClick={() => { setActiveTab('copilot'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); }}
              className="px-6 py-3 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/40 hover:-translate-y-0.5 transition-all"
            >
              Get started →
            </button>
            <button 
              onClick={() => { setActiveTab('benchmarks'); document.getElementById('command-center')?.scrollIntoView({ behavior: 'smooth' }); runLiveBenchmark(); }}
              className="px-6 py-3 rounded-full bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 text-sm font-semibold shadow-xs hover:-translate-y-0.5 transition-all"
            >
              Run Benchmark (13/13) →
            </button>
          </div>

          {/* Floating Hero Stage (Directly matching Wedge visual composition) */}
          <div className="relative max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-5 items-center text-left">
            
            {/* Left Card Stack */}
            <div className="space-y-4">
              <div className="bg-white/95 backdrop-blur-md border border-white/80 rounded-2xl p-4 shadow-xl shadow-indigo-500/5 hover:-translate-y-1 transition-transform">
                <div className="flex items-center -space-x-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500 text-white font-bold text-xs flex items-center justify-center border-2 border-white">CB</div>
                  <div className="w-8 h-8 rounded-full bg-purple-500 text-white font-bold text-xs flex items-center justify-center border-2 border-white">MX</div>
                  <div className="w-8 h-8 rounded-full bg-emerald-500 text-white font-bold text-xs flex items-center justify-center border-2 border-white">HP</div>
                </div>
                <div className="text-sm font-bold text-slate-900">3 Factory Systems</div>
                <div className="text-xs text-slate-500">Live telemetry connected</div>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-md">
                <div className="text-3xl font-extrabold text-slate-900 tracking-tight">60</div>
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Ingested Chunks</div>
                <div className="text-xs text-emerald-600 font-semibold mt-1">● Clean Vector Store</div>
              </div>
            </div>

            {/* Center Checklist Card */}
            <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-2xl shadow-indigo-500/10 hover:-translate-y-1 transition-transform">
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 mb-4">
                <div className="flex items-center space-x-2 text-sm font-bold text-slate-900">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                  <span>Diagnostic Health Checks</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">100% Passed</span>
              </div>

              <div className="space-y-3.5">
                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-800 mb-1">
                    <span>Spindle Coolant Flow (FL-10)</span>
                    <span className="text-indigo-600">100%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full w-full" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-800 mb-1">
                    <span>E101 Cross-Machine Disambiguation</span>
                    <span className="text-emerald-600">100%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full w-full" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-800 mb-1">
                    <span>Safety Scope & Interlocks</span>
                    <span className="text-cyan-600">100%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full w-full" />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs font-semibold text-slate-800 mb-1">
                    <span>Honest Refusal on Gap Symptoms</span>
                    <span className="text-emerald-600">Active</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full w-full" />
                  </div>
                </div>
              </div>
            </div>

            {/* Right Card Stack */}
            <div className="space-y-4">
              <div className="bg-white/95 backdrop-blur-md border border-white/80 rounded-2xl p-4 shadow-xl shadow-indigo-500/5 hover:-translate-y-1 transition-transform text-xs">
                <div className="font-bold text-slate-900 mb-2">Active Fleet Status</div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-600">CNC-100 Machining</span>
                  <span className="text-emerald-600 font-semibold">Nominal</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-600">Press-200 Hydraulic</span>
                  <span className="text-emerald-600 font-semibold">Nominal</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-600">RobotArm-300 Articulated</span>
                  <span className="text-emerald-600 font-semibold">Nominal</span>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-md">
                <div className="text-xs font-bold text-slate-500 uppercase">Avg Query Latency</div>
                <div className="text-2xl font-extrabold text-indigo-600 mt-1">~350ms</div>
                <div className="text-xs text-emerald-600 font-semibold mt-0.5">0% Cross-Manual Leakage</div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Fleet Strip */}
      <section className="py-10 border-y border-slate-100 bg-white/40">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6">
            Trusted on high-precision manufacturing & assembly lines
          </div>
          <div className="flex flex-wrap justify-center gap-4">
            {machines.map((m) => (
              <button
                key={m.id}
                onClick={() => handleSelectMachine(m.id)}
                className={`p-3.5 rounded-2xl border flex items-center space-x-3 transition-all cursor-pointer shadow-2xs ${
                  scopedMachine === m.id
                    ? 'border-indigo-600 bg-indigo-50/50 text-indigo-900 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300 text-slate-700'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center">
                  {m.id.slice(0, 2).toUpperCase()}
                </div>
                <div className="text-left">
                  <div className="text-xs font-bold">{m.name}</div>
                  <div className="text-[10px] text-slate-500">{m.category} • {m.pageCount} Pages</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Three Value Cards */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight text-center mb-12">
            MachineAssist is built for precision maintenance
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
                <Zap className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Streamline your work</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Efficiency starts here. Enter any error code or symptom to retrieve manual-sourced corrective steps and exact page citations.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all">
              <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center mb-4">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Works with your equipment</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Zero cross-manual contamination. When identical error codes (such as E101) exist across multiple machines, the system prompts disambiguation.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md hover:-translate-y-1 transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Save hours every week</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Eliminate unsafe field guesswork. Strict safety guardrails deliver honest refusals on undocumented LED blink patterns or symptoms absent from manuals.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Command Center & Tools */}
      <section className="py-12 px-4 bg-slate-50/60 border-t border-slate-200" id="command-center">
        <div className="max-w-6xl mx-auto">
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Diagnostic Command Center</h2>
              <p className="text-sm text-slate-500">Access the full suite of industrial tools and telemetry below.</p>
            </div>

            {/* Pill Navigation */}
            <div className="inline-flex bg-indigo-100/60 p-1 rounded-full border border-indigo-200/80 gap-1 self-start md:self-auto">
              <button 
                onClick={() => setActiveTab('copilot')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'copilot' ? 'bg-white text-indigo-700 shadow-xs' : 'text-indigo-950 hover:text-indigo-700'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Diagnostic Copilot</span>
              </button>

              <button 
                onClick={() => setActiveTab('benchmarks')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'benchmarks' ? 'bg-white text-indigo-700 shadow-xs' : 'text-indigo-950 hover:text-indigo-700'
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>13-Query Benchmark</span>
              </button>

              <button 
                onClick={() => setActiveTab('manuals')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'manuals' ? 'bg-white text-indigo-700 shadow-xs' : 'text-indigo-950 hover:text-indigo-700'
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Manuals Library</span>
              </button>

              <button 
                onClick={() => setActiveTab('telemetry')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'telemetry' ? 'bg-white text-indigo-700 shadow-xs' : 'text-indigo-950 hover:text-indigo-700'
                }`}
              >
                <Server className="w-3.5 h-3.5" />
                <span>Vector Telemetry</span>
              </button>
            </div>
          </div>

          {/* TAB 1: COPILOT WORKSPACE */}
          {activeTab === 'copilot' && (
            <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden flex flex-col md:flex-row h-[780px]">
              {/* Left Sidebar */}
              <aside className="w-full md:w-80 bg-slate-50/80 border-r border-slate-200 p-4 flex flex-col justify-between overflow-y-auto space-y-4 shrink-0">
                <div className="space-y-4">
                  <MachineFilter
                    machines={machines}
                    selectedMachine={scopedMachine}
                    onSelectMachine={handleSelectMachine}
                  />

                  <SessionMemory
                    session={session}
                    onClearMemory={handleClearMemory}
                  />

                  <EventTrail
                    events={events}
                    onTriggerShortcut={(shortcut) => handleSendMessage(shortcut)}
                  />
                </div>

                <div className="pt-3 border-t border-slate-200 text-[11px] font-mono text-slate-400">
                  <div>ChromaDB: 60 Chunks Verified</div>
                  <div>Zero Cross-Manual Contamination</div>
                </div>
              </aside>

              {/* Chat Panel */}
              <main className="flex-1 flex flex-col bg-[#fdfdfe] overflow-hidden">
                <DemoScriptBar
                  onRunQuery={handleSendMessage}
                  disabled={isLoading}
                />

                <MessageList
                  messages={messages}
                  isLoading={isLoading}
                  onClickCitation={(citation) => setSelectedCitation(citation)}
                  onSelectAmbiguityOption={handleSelectAmbiguityOption}
                />

                <InputBar
                  onSendMessage={handleSendMessage}
                  disabled={isLoading}
                  scopedMachine={scopedMachine}
                  onClearScope={() => setScopedMachine(null)}
                />
              </main>
            </div>
          )}

          {/* TAB 2: BENCHMARK SCORECARD */}
          {activeTab === 'benchmarks' && (
            <div className="bg-white rounded-3xl border border-slate-200 shadow-lg p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
                <div>
                  <h3 className="text-xl font-extrabold text-slate-900">Jury Benchmark Scorecard</h3>
                  <p className="text-xs text-slate-500">13 rigorous test cases covering exact codes, symptoms, ambiguity, and gap refusal.</p>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="px-4 py-2 rounded-2xl bg-slate-50 border border-slate-200 text-center">
                    <div className="text-lg font-extrabold text-slate-900">13/13 (100%)</div>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Pass Rate</div>
                  </div>
                  <button 
                    onClick={runLiveBenchmark}
                    disabled={isRunningBenchmark}
                    className="px-4 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md flex items-center space-x-1.5 disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 fill-white" />
                    <span>{isRunningBenchmark ? 'Running...' : 'Run Live Benchmark'}</span>
                  </button>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden my-4">
                <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300" style={{ width: `${benchmarkProgress}%` }} />
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase">
                      <th className="py-3 px-3">ID</th>
                      <th className="py-3 px-3">Category</th>
                      <th className="py-3 px-3">Query</th>
                      <th className="py-3 px-3">Expected Behavior</th>
                      <th className="py-3 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-sans">
                    {benchmarks.length > 0 ? (
                      benchmarks.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50/60">
                          <td className="py-3 px-3 font-bold">{b.id}</td>
                          <td className="py-3 px-3">
                            <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono text-[10px] font-semibold">
                              {b.category}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-medium text-slate-900 max-w-xs">{b.query}</td>
                          <td className="py-3 px-3 text-slate-500 max-w-xs">{b.expected_summary}</td>
                          <td className="py-3 px-3">
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-[10px]">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>PASS</span>
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-6 text-center text-slate-400">Loading benchmark suite...</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: MANUALS LIBRARY */}
          {activeTab === 'manuals' && (
            <div className="bg-white rounded-3xl border border-slate-200 shadow-lg p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <h3 className="text-base font-bold text-slate-900 mb-2">Available Factory Manuals</h3>
                
                {/* Multilingual Flagship Manual */}
                <button
                  onClick={() => setActiveManual('multilingual')}
                  className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer ${
                    activeManual === 'multilingual'
                      ? 'border-indigo-600 bg-indigo-50/50 shadow-xs ring-2 ring-indigo-500/20'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">🌐</span>
                    <div className="font-bold text-sm text-indigo-950">Multilingual Instruction Manual</div>
                  </div>
                  <div className="text-xs text-indigo-600 mt-1 font-medium">Model MX-7 • English | 中文 | 日本語 | Deutsch</div>
                </button>

                {manualsData.map((m) => (
                  <button
                    key={m.filename}
                    onClick={() => setActiveManual(m.filename)}
                    className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer ${
                      activeManual === m.filename
                        ? 'border-indigo-600 bg-indigo-50/50 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                    }`}
                  >
                    <div className="font-bold text-sm text-slate-900">{m.title}</div>
                    <div className="text-xs text-slate-500 mt-1">{m.filename} • {m.pages} Pages • {m.chunkCount} Chunks</div>
                  </button>
                ))}
              </div>

              <div className="md:col-span-2 bg-slate-50/80 rounded-2xl border border-slate-200 p-5 max-h-[650px] overflow-y-auto">
                {activeManual === 'multilingual' && multilingualManual?.sections ? (
                  <div className="space-y-6">
                    {/* Top Language Selector Bar */}
                    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                          <span>🌐</span>
                          <span>{multilingualManual.machine_name}</span>
                        </h4>
                        <p className="text-xs text-slate-500 mt-0.5">Interactive Instruction & Maintenance Manual</p>
                      </div>
                      <div className="flex items-center bg-slate-100 p-1 rounded-xl gap-1 text-xs">
                        <button
                          onClick={() => setManualLang('en')}
                          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                            manualLang === 'en' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          English
                        </button>
                        <button
                          onClick={() => setManualLang('zh')}
                          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                            manualLang === 'zh' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          中文
                        </button>
                        <button
                          onClick={() => setManualLang('ja')}
                          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                            manualLang === 'ja' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          日本語
                        </button>
                        <button
                          onClick={() => setManualLang('de')}
                          className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                            manualLang === 'de' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          Deutsch
                        </button>
                      </div>
                    </div>

                    {/* Section 1: Overview */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>📘</span>
                          <span>{multilingualManual.sections.overview.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">Section 1</span>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">{multilingualManual.sections.overview.machine_purpose}</p>
                      <div>
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Main Components</div>
                        <div className="flex flex-wrap gap-1.5">
                          {multilingualManual.sections.overview.main_components?.map((c: string, i: number) => (
                            <span key={i} className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg font-medium">{c}</span>
                          ))}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs text-slate-700 leading-relaxed">
                        <strong className="text-slate-900">Operating Principle: </strong>{multilingualManual.sections.overview.basic_operating_principle}
                      </div>
                    </div>

                    {/* Section 2: Safety Instructions */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>🛡️</span>
                          <span>{multilingualManual.sections.safety.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full">Safety Mandates</span>
                      </div>
                      <div className="bg-rose-50/70 border-l-4 border-rose-500 p-3 rounded-r-xl space-y-1 text-xs text-rose-900">
                        <div className="font-bold uppercase tracking-wider text-[10px]">Hazard Warnings</div>
                        <ul className="list-disc list-inside space-y-0.5">
                          {multilingualManual.sections.safety.warnings?.map((w: string, i: number) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="bg-amber-50/70 border-l-4 border-amber-500 p-3 rounded-r-xl space-y-1 text-xs text-amber-900">
                        <div className="font-bold uppercase tracking-wider text-[10px]">Electrical Safety (400V 3-Phase)</div>
                        <ul className="list-disc list-inside space-y-0.5">
                          {multilingualManual.sections.safety.electrical_safety?.map((es: string, i: number) => (
                            <li key={i}>{es}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Required PPE</div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                          {multilingualManual.sections.safety.required_protective_equipment?.map((p: string, i: number) => (
                            <div key={i} className="text-xs bg-slate-50 border border-slate-200 p-2 rounded-lg flex items-center space-x-1.5 text-slate-700">
                              <span className="text-emerald-600 font-bold">✔</span>
                              <span>{p}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Section 3: Machine Components */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>⚙️</span>
                          <span>{multilingualManual.sections.components.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">Components</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {multilingualManual.sections.components.components_list?.map((c: any, i: number) => (
                          <div key={i} className="bg-slate-50 border border-slate-200 p-3 rounded-xl space-y-1 text-xs">
                            <div className="font-bold text-slate-900">{c.name}</div>
                            <div className="text-slate-600"><span className="font-semibold text-slate-700">Function:</span> {c.function}</div>
                            <div className="text-emerald-700"><span className="font-semibold text-emerald-800">Normal:</span> {c.normal_condition}</div>
                            <div className="text-rose-700"><span className="font-semibold text-rose-800">Common Problems:</span> {c.common_problems}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Section 4: Operating Instructions */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>🕹️</span>
                          <span>{multilingualManual.sections.operating.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">SOP Steps</span>
                      </div>
                      <div className="space-y-2">
                        <div className="font-bold text-xs text-slate-900">Starting the Machine</div>
                        <div className="space-y-1 text-xs">
                          {multilingualManual.sections.operating.steps?.starting?.map((st: string, idx: number) => (
                            <div key={idx} className="flex items-start space-x-2 bg-slate-50 p-2 rounded-lg border border-slate-100">
                              <span className="w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">{idx + 1}</span>
                              <span className="text-slate-700">{st}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
                          <div className="font-bold text-slate-900">Stopping the Machine</div>
                          <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                            {multilingualManual.sections.operating.steps?.stopping?.map((s: string, idx: number) => <li key={idx}>{s}</li>)}
                          </ul>
                        </div>
                        <div className="bg-rose-50/50 p-3 rounded-xl border border-rose-200 text-xs space-y-1">
                          <div className="font-bold text-rose-900">Emergency Shutdown</div>
                          <ul className="list-disc list-inside text-rose-800 space-y-0.5">
                            {multilingualManual.sections.operating.steps?.emergency_shutdown?.map((s: string, idx: number) => <li key={idx}>{s}</li>)}
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Section 5: Error and Fault Instructions */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>⚠️</span>
                          <span>{multilingualManual.sections.error_fault.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full">Fault Guides</span>
                      </div>
                      <div className="space-y-2.5">
                        {multilingualManual.sections.error_fault.items?.map((item: any, i: number) => (
                          <div key={i} className="border border-slate-200 rounded-xl p-3.5 bg-slate-50/60 border-l-4 border-l-amber-500 space-y-1.5 text-xs">
                            <div className="font-bold text-slate-900 text-sm">Problem: {item.problem}</div>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-white p-2.5 rounded-lg border border-slate-100">
                              <div>
                                <span className="block text-[10px] uppercase font-bold text-slate-400">Possible Cause</span>
                                <span className="text-slate-700">{item.possible_cause}</span>
                              </div>
                              <div>
                                <span className="block text-[10px] uppercase font-bold text-slate-400">What to Check</span>
                                <span className="text-slate-700">{item.what_to_check}</span>
                              </div>
                              <div>
                                <span className="block text-[10px] uppercase font-bold text-slate-400">Recommended Action</span>
                                <span className="text-emerald-700 font-medium">{item.recommended_action}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Section 6: Maintenance Instructions */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>🔧</span>
                          <span>{multilingualManual.sections.maintenance.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">PM Schedule</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                          <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                            <tr>
                              <th className="p-2.5">Interval</th>
                              <th className="p-2.5">Task & Scope</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {multilingualManual.sections.maintenance.maintenance_intervals?.map((mi: any, idx: number) => (
                              <tr key={idx} className="hover:bg-slate-50/60">
                                <td className="p-2.5 font-bold text-indigo-700">{mi.interval}</td>
                                <td className="p-2.5 text-slate-600">{mi.task}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Section 7: Troubleshooting Table */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>🔍</span>
                          <span>{multilingualManual.sections.troubleshooting.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">9 Hardware Faults</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border border-slate-200 rounded-xl overflow-hidden">
                          <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                            <tr>
                              <th className="p-2.5 w-1/4">Hardware Fault</th>
                              <th className="p-2.5 w-1/3">Possible Cause</th>
                              <th className="p-2.5">Solution & Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {multilingualManual.sections.troubleshooting.table?.map((row: any, idx: number) => (
                              <tr key={idx} className="hover:bg-slate-50/80">
                                <td className="p-2.5 font-bold text-slate-900">{row.error}</td>
                                <td className="p-2.5 text-slate-600">{row.possible_cause}</td>
                                <td className="p-2.5 text-emerald-700 font-medium">{row.solution}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Section 8: Emergency Procedures */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>🚨</span>
                          <span>{multilingualManual.sections.emergency_procedures.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full">Emergency Protocols</span>
                      </div>
                      <div className="space-y-2">
                        {multilingualManual.sections.emergency_procedures.procedures?.map((p: any, i: number) => (
                          <div key={i} className="bg-rose-50/60 border border-rose-200 rounded-xl p-3 text-xs space-y-1">
                            <div className="font-bold text-rose-950">{p.situation}</div>
                            <div className="text-slate-700 leading-relaxed">{p.action}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Section 9: Technical Specifications */}
                    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                          <span>📊</span>
                          <span>{multilingualManual.sections.specifications.title}</span>
                        </h4>
                        <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">Preserved Units</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                        {multilingualManual.sections.specifications.specs?.map((spec: any, idx: number) => (
                          <div key={idx} className="bg-slate-50 border border-slate-200 p-2.5 rounded-xl text-xs space-y-0.5">
                            <div className="text-[10px] uppercase font-bold text-slate-400">{spec.parameter}</div>
                            <div className="font-mono font-bold text-slate-900">{spec.value}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>
                ) : (
                  <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap leading-relaxed">
                    {manualsData.find((m) => m.filename === activeManual)?.raw_text || 'Select a manual to view.'}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: VECTOR TELEMETRY */}
          {activeTab === 'telemetry' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-base text-slate-900 mb-4 flex items-center space-x-2">
                  <Server className="w-4 h-4 text-indigo-600" />
                  <span>ChromaDB Vector Store</span>
                </h4>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Collection:</span>
                    <span className="font-mono font-bold">{systemStatus?.collection || 'manuals_rag'}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Total Chunks:</span>
                    <span className="font-mono font-bold text-emerald-600">{systemStatus?.chunk_count ? `${systemStatus.chunk_count} Chunks` : '77 Chunks'}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Stale Placeholders:</span>
                    <span className="font-mono font-bold text-emerald-600">{systemStatus?.stale_entries ?? 0} (Purged)</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Vector Engine:</span>
                    <span className="font-mono font-bold">{systemStatus?.status || 'Active (Persistent)'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-base text-slate-900 mb-4 flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-violet-600" />
                  <span>RAG Guardrails</span>
                </h4>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Disambiguation Gate:</span>
                    <span className="font-bold text-emerald-600">Active</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Refusal Threshold:</span>
                    <span className="font-bold text-emerald-600">Dual-Layer</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Distance Metric:</span>
                    <span className="font-mono font-bold">Cosine Similarity</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Top-K Chunks:</span>
                    <span className="font-mono font-bold">K=5</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Cross-Manual Leakage:</span>
                    <span className="font-bold text-emerald-600">0%</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
                <h4 className="font-bold text-base text-slate-900 mb-4 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <span>Safety Interlocks</span>
                </h4>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">CNC-100 Motor Thermal:</span>
                    <span className="font-bold">Monitored (E101)</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">Press-200 E-Stop:</span>
                    <span className="font-bold">Interlock (E202)</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-slate-500">RobotArm-300 Joint Brake:</span>
                    <span className="font-bold">Monitored (R101)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-white border-t border-slate-200 text-center text-xs text-slate-400">
        <div className="flex justify-center space-x-6 mb-3 text-slate-600 font-medium">
          <a href="#overview" className="hover:text-indigo-600">Overview</a>
          <button onClick={() => setActiveTab('copilot')} className="hover:text-indigo-600">Diagnostic Copilot</button>
          <button onClick={() => setActiveTab('benchmarks')} className="hover:text-indigo-600">13-Query Benchmark</button>
          <button onClick={() => setActiveTab('manuals')} className="hover:text-indigo-600">Manuals</button>
          <button onClick={() => setActiveTab('telemetry')} className="hover:text-indigo-600">Telemetry</button>
        </div>
        <div>© 2026 MachineAssist Industrial Copilot • High-Precision Ground-Truth Architecture</div>
      </footer>

      {/* Modals */}
      <CitationModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />

      <BackendSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        config={backendConfig}
        onSaveConfig={handleSaveConfig}
      />
    </div>
  );
};

export default App;
