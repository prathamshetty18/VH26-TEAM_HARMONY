import React from 'react';
import type { Machine } from '../../types';
import { Layers, ChevronDown, BookOpen } from 'lucide-react';

interface MachineFilterProps {
  machines: Machine[];
  selectedMachine: string | null;
  onSelectMachine: (machineId: string | null) => void;
}

export const MachineFilter: React.FC<MachineFilterProps> = ({
  machines,
  selectedMachine,
  onSelectMachine,
}) => {
  return (
    <div className="space-y-4">
      {/* Header section with dropdown selector */}
      <div>
        <div className="flex items-center justify-between text-xs md:text-sm font-mono uppercase tracking-wider text-slate-600 font-bold mb-2">
          <span>Machine Filter</span>
          {selectedMachine && (
            <button
              onClick={() => onSelectMachine(null)}
              className="text-xs text-slate-500 hover:text-slate-800 underline normal-case cursor-pointer"
            >
              Clear filter
            </button>
          )}
        </div>

        <div className="relative">
          <select
            value={selectedMachine || ''}
            onChange={(e) => onSelectMachine(e.target.value ? e.target.value : null)}
            className="w-full bg-white border border-slate-300 rounded px-3 py-2 text-xs md:text-sm text-slate-800 font-mono focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500 appearance-none cursor-pointer shadow-xs"
          >
            <option value="">All Machines (Auto-detect)</option>
            {machines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.id} — {m.name}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
        </div>
      </div>

      {/* Active units list */}
      <div>
        <div className="flex items-center justify-between text-xs md:text-sm font-mono uppercase tracking-wider text-slate-600 font-bold mb-2">
          <span>Active Units</span>
          <span className="text-xs text-slate-400">{machines.length} Registered</span>
        </div>

        <div className="space-y-2">
          {machines.map((machine) => {
            const isSelected = selectedMachine === machine.id;
            return (
              <button
                key={machine.id}
                onClick={() => onSelectMachine(isSelected ? null : machine.id)}
                className={`w-full text-left p-2.5 rounded-md border transition-all flex items-center justify-between cursor-pointer ${
                  isSelected
                    ? 'bg-slate-900 border-slate-900 text-white shadow-xs'
                    : 'bg-white border-slate-200 text-slate-800 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div
                    className={`w-6 h-6 rounded flex items-center justify-center shrink-0 ${
                      isSelected ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                  </div>
                  <div className="truncate">
                    <div className="font-mono text-xs md:text-sm font-bold tracking-tight truncate">
                      {machine.id}
                    </div>
                    <div
                      className={`text-xs truncate ${
                        isSelected ? 'text-slate-300' : 'text-slate-500'
                      }`}
                    >
                      {machine.name}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1 shrink-0 ml-2">
                  <span
                    className={`text-[10px] md:text-xs font-mono px-2 py-0.5 rounded border uppercase flex items-center space-x-1 ${
                      isSelected
                        ? 'bg-slate-800 border-slate-700 text-emerald-300'
                        : 'bg-slate-50 border-slate-200 text-slate-600'
                    }`}
                  >
                    <BookOpen className="w-3 h-3" />
                    <span>MANUAL</span>
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
