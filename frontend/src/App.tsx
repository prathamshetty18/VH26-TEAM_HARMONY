import React, { useState, useEffect } from 'react';
import { TopBar } from './components/TopBar';
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [events, setEvents] = useState<EventTrailItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [backendConfig, setBackendConfig] = useState<BackendConfig>(diagnosticService.getConfig());
  const [isLiveActive, setIsLiveActive] = useState<boolean>(false);

  // Sync session state to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('machineassist_session', JSON.stringify(session));
  }, [session]);

  // Probe backend health & load machines on mount or config change
  useEffect(() => {
    const loadData = async () => {
      const isHealthy = await diagnosticService.checkBackendHealth();
      setIsLiveActive(isHealthy);
      const data = await diagnosticService.getMachines();
      setMachines(data);
    };
    loadData();
  }, [backendConfig]);

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

  // Handle ambiguity option selection
  const handleSelectAmbiguityOption = (option: AmbiguityOption) => {
    handleSelectMachine(option.machine);
    const query = option.queryHint || `Troubleshoot ${session.lastError || 'fault'} on ${option.machine}`;
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

  return (
    <div className="flex flex-col h-screen w-screen bg-[#f1f3f6] overflow-hidden">
      {/* Top Bar */}
      <TopBar
        sessionId={session.sessionId}
        onResetSession={handleResetSession}
        config={backendConfig}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isLiveActive={isLiveActive}
        machines={machines}
        selectedMachine={scopedMachine}
        onSelectMachine={handleSelectMachine}
      />

      {/* Main 3-column / 2-panel industrial interface */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-72 lg:w-80 bg-white border-r border-slate-200 flex flex-col justify-between overflow-y-auto p-3.5 space-y-4 shrink-0 shadow-2xs">
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

          <div className="pt-3 border-t border-slate-100 text-[10px] font-mono text-slate-400 space-y-0.5">
            <div>© 2024 MachineAssist Diagnostic Core</div>
            <div>Phase 7 Verified RAG Ground-Truth Architecture</div>
          </div>
        </aside>

        {/* Center / Right Chat Workspace */}
        <main className="flex-1 flex flex-col bg-[#f4f6f9] overflow-hidden">
          {/* Demo Script Quick Action Bar */}
          <DemoScriptBar
            onRunQuery={handleSendMessage}
            disabled={isLoading}
          />

          {/* Messages Feed */}
          <MessageList
            messages={messages}
            isLoading={isLoading}
            onClickCitation={(citation) => setSelectedCitation(citation)}
            onSelectAmbiguityOption={handleSelectAmbiguityOption}
          />

          {/* Fixed Input Bar */}
          <InputBar
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            scopedMachine={scopedMachine}
            onClearScope={() => setScopedMachine(null)}
          />
        </main>
      </div>

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
