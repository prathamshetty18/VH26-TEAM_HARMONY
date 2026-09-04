import React from 'react';
import { Cpu, RefreshCw, Settings } from 'lucide-react';
import type { BackendConfig } from '../types';

interface TopBarProps {
  sessionId: string;
  onResetSession: () => void;
  config: BackendConfig;
  onOpenSettings: () => void;
  isLiveActive: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  sessionId,
  onResetSession,
  config,
  onOpenSettings,
  isLiveActive,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 px-5 flex items-center justify-between shadow-xs select-none sticky top-0 z-30">
      {/* Product branding */}
      <div className="flex items-center space-x-3.5">
        <div className="w-9 h-9 rounded bg-slate-900 flex items-center justify-center text-white shadow-xs">
          <Cpu className="w-5 h-5 text-slate-100" />
        </div>
        <div className="flex items-baseline space-x-2.5">
          <span className="font-bold text-lg md:text-xl tracking-tight text-slate-900">MachineAssist</span>
          <span className="text-xs font-mono uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200 font-semibold">
            HMI v2.4
          </span>
        </div>
      </div>

      {/* Center status indicator */}
      <div className="hidden md:flex items-center space-x-4 text-xs md:text-sm font-mono">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="tracking-wide">
            {isLiveActive ? 'BACKEND CONNECTED' : 'DIAGNOSTIC ENGINE READY'}
          </span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center space-x-3.5">
        <div className="flex items-center space-x-2 text-xs md:text-sm text-slate-700 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded font-mono">
          <span className="text-slate-400 font-sans text-xs">SESSION:</span>
          <span className="font-bold text-slate-900 tracking-wider">{sessionId}</span>
        </div>

        <button
          onClick={onResetSession}
          title="Reset current session context"
          className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 rounded transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        <button
          onClick={onOpenSettings}
          title="Diagnostic Connection Config"
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs md:text-sm text-slate-700 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded transition-colors font-mono cursor-pointer font-medium"
        >
          <Settings className="w-4 h-4 text-slate-600" />
          <span className="uppercase text-xs font-semibold">
            {config.mode === 'live' ? 'Live API' : 'Demo Mode'}
          </span>
        </button>
      </div>
    </header>
  );
};
