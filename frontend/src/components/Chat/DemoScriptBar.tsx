import React from 'react';
import { PlayCircle, CheckCircle2, Split, ShieldAlert } from 'lucide-react';

interface DemoScriptBarProps {
  onRunQuery: (query: string) => void;
  disabled?: boolean;
}

export const DemoScriptBar: React.FC<DemoScriptBarProps> = ({ onRunQuery, disabled }) => {
  const demoQueries = [
    {
      id: '1',
      title: '1. Exact Code',
      badge: 'NORMAL + CITATION',
      query: 'What does E101 mean on CNC-100?',
      icon: CheckCircle2,
      color: 'hover:border-emerald-400 hover:bg-emerald-50/40 hover:shadow-xs',
      badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    },
    {
      id: '2',
      title: '2. Symptom Search',
      badge: 'SEMANTIC RAG',
      query: 'Why is Press-200 stopping due to oil pressure?',
      icon: PlayCircle,
      color: 'hover:border-blue-400 hover:bg-blue-50/40 hover:shadow-xs',
      badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
    },
    {
      id: '3',
      title: '3. Ambiguity Check',
      badge: 'CLARIFICATION CARD',
      query: 'What does E101 mean?',
      icon: Split,
      color: 'hover:border-amber-400 hover:bg-amber-50/40 hover:shadow-xs',
      badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
    },
    {
      id: '4',
      title: '4. Insufficient Info',
      badge: 'CALM REFUSAL',
      query: 'How do I replace spindle bearing on CNC-100?',
      icon: ShieldAlert,
      color: 'hover:border-slate-400 hover:bg-slate-100 hover:shadow-xs',
      badgeColor: 'bg-slate-100 text-slate-700 border-slate-200',
    },
  ];

  return (
    <div className="bg-white border-b border-slate-200 px-5 py-3.5 shadow-2xs">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs md:text-sm font-mono uppercase tracking-wider text-slate-700 font-bold flex items-center space-x-2">
          <PlayCircle className="w-4 h-4 text-slate-600" />
          <span>Demo Script Sequence (Verified Section 7 Queries)</span>
        </span>
        <span className="text-xs text-slate-400 font-mono hidden sm:inline">
          One-click test triggers for presentation
        </span>
      </div>

      {/* 2x2 spacious grid: 1 next to 2 on top row; 3 below 1, 4 below 2 on second row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {demoQueries.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              disabled={disabled}
              onClick={() => onRunQuery(item.query)}
              className={`text-left p-3 rounded-lg border border-slate-200 bg-white transition-all shadow-2xs group cursor-pointer disabled:opacity-50 ${item.color}`}
            >
              <div className="flex items-center justify-between mb-1.5 gap-2">
                <span className="text-xs md:text-sm font-bold text-slate-900 flex items-center space-x-2 font-mono whitespace-nowrap">
                  <Icon className="w-4 h-4 text-slate-600 group-hover:text-black shrink-0" />
                  <span>{item.title}</span>
                </span>
                <span
                  className={`text-[10px] md:text-xs font-mono px-2 py-0.5 rounded border uppercase font-bold whitespace-nowrap shrink-0 ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              </div>
              <div className="text-xs md:text-sm text-slate-600 font-mono-code group-hover:text-slate-900 leading-snug">
                "{item.query}"
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
