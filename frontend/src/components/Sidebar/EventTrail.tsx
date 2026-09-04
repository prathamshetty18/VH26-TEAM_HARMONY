import React from 'react';
import type { EventTrailItem } from '../../types';
import { Terminal, CornerDownRight, ArrowRight } from 'lucide-react';

interface EventTrailProps {
  events: EventTrailItem[];
  onTriggerShortcut?: (shortcutQuery: string) => void;
}

export const EventTrail: React.FC<EventTrailProps> = ({ events, onTriggerShortcut }) => {
  if (events.length === 0) {
    return (
      <div className="border border-dashed border-slate-200 rounded-md p-3 text-center text-slate-400 text-xs font-mono">
        No context switch events recorded
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs md:text-sm font-mono uppercase tracking-wider text-slate-600 font-bold">
        <span className="flex items-center space-x-2">
          <Terminal className="w-3.5 h-3.5 text-slate-500" />
          <span>Event Trail</span>
        </span>
        <span className="text-xs text-slate-400">{events.length} logs</span>
      </div>

      <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
        {events.slice(-6).map((item) => (
          <div
            key={item.id}
            className="p-2.5 bg-slate-50 border border-slate-200 rounded-md font-mono text-xs text-slate-700"
          >
            <div className="flex items-start justify-between">
              <span className="text-slate-400 text-[11px]">{item.timestamp}</span>
              {item.machine && (
                <span className="bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded text-[11px] font-bold">
                  {item.machine}
                </span>
              )}
            </div>
            <div className="mt-1 text-slate-900 text-xs leading-normal">
              {item.text}
            </div>

            {item.shortcut && onTriggerShortcut && (
              <button
                onClick={() => onTriggerShortcut(item.shortcut!)}
                className="mt-2 w-full flex items-center justify-between px-2.5 py-1.5 bg-white hover:bg-slate-100 border border-slate-200 hover:border-slate-300 rounded text-xs text-slate-700 hover:text-slate-900 transition-colors cursor-pointer font-medium"
              >
                <span className="flex items-center space-x-1.5 truncate">
                  <CornerDownRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">{item.shortcut}</span>
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
