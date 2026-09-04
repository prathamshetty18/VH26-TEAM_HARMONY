import React, { useState, useRef } from 'react';
import { ArrowRight, Terminal } from 'lucide-react';

interface InputBarProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  scopedMachine: string | null;
  onClearScope?: () => void;
}

export const InputBar: React.FC<InputBarProps> = ({
  onSendMessage,
  disabled,
  scopedMachine,
  onClearScope,
}) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'Escape') {
      setInput('');
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-3.5 space-y-2.5 select-none">
      <form onSubmit={handleSubmit} className="flex items-center space-x-2.5">
        <div className="relative flex-1 flex items-center">
          <div className="absolute left-3.5 text-slate-400 pointer-events-none">
            <Terminal className="w-5 h-5" />
          </div>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder={
              scopedMachine
                ? `Describe fault or enter error code for ${scopedMachine} (e.g. E101)...`
                : "Describe the fault, or enter an error code (e.g. E101)..."
            }
            className="w-full bg-slate-50 hover:bg-white focus:bg-white border border-slate-300 focus:border-slate-800 rounded-md py-2.5 pl-11 pr-32 text-sm md:text-base font-mono text-slate-900 placeholder:text-slate-400 placeholder:font-sans focus:outline-none focus:ring-1 focus:ring-slate-800 transition-all shadow-inner"
          />

          {scopedMachine && (
            <div className="absolute right-2.5 flex items-center space-x-1.5 bg-slate-200 text-slate-800 px-2.5 py-1 rounded text-xs md:text-sm font-mono font-semibold">
              <span>SCOPE: {scopedMachine}</span>
              {onClearScope && (
                <button
                  type="button"
                  onClick={onClearScope}
                  className="hover:text-black ml-1 font-bold cursor-pointer"
                  title="Clear machine scope"
                >
                  ×
                </button>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="bg-slate-900 hover:bg-black disabled:bg-slate-300 text-white px-5 py-2.5 rounded-md font-mono text-sm font-semibold flex items-center space-x-2 transition-colors shrink-0 shadow-xs cursor-pointer disabled:cursor-not-allowed"
        >
          <span>Send</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
        <div className="flex items-center space-x-4">
          <span>
            <strong className="text-slate-600 font-medium">RETURN</strong> to submit
          </span>
          <span>
            <strong className="text-slate-600 font-medium">ESC</strong> clear
          </span>
          <span className="hidden sm:inline">
            <strong className="text-slate-600 font-medium">HOTKEY:</strong> click machine to scope
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-emerald-600 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>DIAGNOSTIC ENGINE READY</span>
        </div>
      </div>
    </div>
  );
};
