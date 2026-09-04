import React from 'react';
import type { SessionMemoryState } from '../../types';
import { History } from 'lucide-react';

interface SessionMemoryProps {
  session: SessionMemoryState;
  onClearMemory: () => void;
}

export const SessionMemory: React.FC<SessionMemoryProps> = ({ session, onClearMemory }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-md p-3.5 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2 text-slate-800 font-bold uppercase tracking-wider text-xs md:text-sm font-mono">
          <History className="w-4 h-4 text-slate-500" />
          <span>Session Memory</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="text-xs font-mono text-slate-500 font-semibold">ACTIVE</span>
        </div>
      </div>

      {/* Memory Fields */}
      <div className="space-y-2.5 font-mono">
        <div className="flex items-center justify-between text-xs md:text-sm">
          <span className="text-slate-500">Last machine:</span>
          <span
            className={`font-semibold px-2 py-0.5 rounded border text-xs md:text-sm ${
              session.lastMachine
                ? 'bg-slate-100 border-slate-300 text-slate-900'
                : 'bg-slate-50 border-slate-200 text-slate-400 font-normal italic'
            }`}
          >
            {session.lastMachine || 'None'}
          </span>
        </div>

        <div className="flex items-center justify-between text-xs md:text-sm">
          <span className="text-slate-500">Last error:</span>
          <span
            className={`font-semibold px-2 py-0.5 rounded border text-xs md:text-sm ${
              session.lastError
                ? 'bg-amber-50 border-amber-300 text-amber-900'
                : 'bg-slate-50 border-slate-200 text-slate-400 font-normal italic'
            }`}
          >
            {session.lastError || 'None'}
          </span>
        </div>

        <div className="pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <span>Persisted across turns</span>
          {(session.lastMachine || session.lastError) && (
            <button
              onClick={onClearMemory}
              className="text-slate-600 hover:text-red-600 underline cursor-pointer font-medium"
            >
              Reset
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
