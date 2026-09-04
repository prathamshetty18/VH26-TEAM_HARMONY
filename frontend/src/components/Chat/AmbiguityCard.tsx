import React from 'react';
import type { Message, AmbiguityOption } from '../../types';
import { HelpCircle, ChevronRight } from 'lucide-react';

interface AmbiguityCardProps {
  message: Message;
  onSelectOption: (option: AmbiguityOption) => void;
}

export const AmbiguityCard: React.FC<AmbiguityCardProps> = ({
  message,
  onSelectOption,
}) => {
  return (
    <div className="bg-white border-2 border-slate-300 rounded-lg p-5 shadow-xs space-y-4 max-w-3xl">
      {/* Ambiguity Header */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center shrink-0">
          <HelpCircle className="w-5 h-5 text-slate-700" />
        </div>
        <div>
          <div className="text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold">
            Ambiguity Detected — Machine Scope Required
          </div>
          <p className="text-base md:text-lg font-semibold text-slate-900 mt-1 leading-snug">
            {message.ambiguityPrompt ||
              'That error code exists on more than one machine. Which one are you asking about?'}
          </p>
        </div>
      </div>

      {/* Clickable Option Buttons */}
      <div className="space-y-2.5 pt-1 pl-11">
        {message.ambiguityOptions?.map((option, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectOption(option)}
            className="w-full text-left p-3.5 rounded-md border border-slate-200 hover:border-slate-400 bg-slate-50/80 hover:bg-slate-100 transition-all flex items-center justify-between group cursor-pointer shadow-2xs"
          >
            <div className="min-w-0 pr-3">
              <div className="text-sm md:text-base font-mono font-bold text-slate-900 group-hover:text-black flex items-center space-x-2">
                <span className="bg-white px-2 py-0.5 rounded border border-slate-200 shadow-2xs text-xs md:text-sm">
                  {option.machine}
                </span>
                <span className="font-sans font-medium text-slate-800 text-sm md:text-base">
                  {option.label.includes('—') ? option.label.split('—')[1]?.trim() : (option.description || option.label)}
                </span>
              </div>
            </div>
            <div className="shrink-0 flex items-center justify-center w-7 h-7 rounded bg-white border border-slate-200 group-hover:border-slate-400 group-hover:bg-slate-900 group-hover:text-white transition-colors">
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white" />
            </div>
          </button>
        ))}
      </div>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs md:text-sm text-slate-400 font-mono pl-11">
        <span>Click to resolve scope with session memory</span>
        <span>{message.timestamp}</span>
      </div>
    </div>
  );
};
