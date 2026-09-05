import React, { useState, useRef } from 'react';
import { Terminal, AlertCircle, Edit3 } from 'lucide-react';
import { speechService } from '../../services/speechService';

interface InputBarProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  scopedMachine: string | null;
  onClearScope?: () => void;
  voiceEnabled?: boolean;
  baseUrl?: string;
}

export const InputBar: React.FC<InputBarProps> = ({
  onSendMessage,
  disabled,
  scopedMachine,
  onClearScope,
  voiceEnabled = true,
  baseUrl = 'http://localhost:8000',
}) => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = input.trim();
    if (!query || disabled || isRecording) return;

    // Send the exact text currently in the input box directly to the existing pipeline
    onSendMessage(query);
    setInput('');
    setVoiceError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'Escape') {
      setInput('');
      setVoiceError(null);
    }
  };

  const stopFnRef = useRef<(() => void) | null>(null);

  // 1. Click Microphone -> Start Recording / Speak
  const handleToggleSpeak = () => {
    if (disabled || !voiceEnabled) return;

    if (isRecording) {
      if (stopFnRef.current) {
        stopFnRef.current();
        stopFnRef.current = null;
      }
      setIsRecording(false);
      return;
    }

    setVoiceError(null);

    const controller = speechService.listenSpeech({
      baseUrl,
      onStart: () => {
        setIsRecording(true);
      },
      onResult: (transcript: string) => {
        setInput(transcript);
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      },
      onError: (errMsg: string) => {
        setVoiceError(errMsg);
      },
      onEnd: () => {
        setIsRecording(false);
        stopFnRef.current = null;
      },
    });

    stopFnRef.current = controller.stop;
  };

  // Edit button: Focuses the input box for direct user editing
  const handleEditClick = () => {
    if (inputRef.current) {
      inputRef.current.focus();
      // Place cursor at end of input
      const len = inputRef.current.value.length;
      inputRef.current.setSelectionRange(len, len);
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-3.5 space-y-2 select-none transition-all">
      {/* Voice Error Notification (if permission denied or API fails) */}
      {voiceError && (
        <div className="flex items-center justify-between text-xs text-red-600 bg-red-50 border border-red-200 rounded-md py-1.5 px-3 font-sans animate-in fade-in">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{voiceError}</span>
          </div>
          <button
            type="button"
            onClick={() => setVoiceError(null)}
            className="text-red-400 hover:text-red-700 font-bold ml-2 cursor-pointer"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="flex items-center space-x-2">
        {/* MICROPHONE BUTTON: "🎤 Speak" / "🔴 Listening..." */}
        {voiceEnabled && (
          <button
            type="button"
            onClick={handleToggleSpeak}
            disabled={disabled}
            className={`px-3.5 py-2.5 rounded-md font-mono text-xs md:text-sm font-semibold flex items-center space-x-2 transition-all shrink-0 cursor-pointer shadow-xs disabled:cursor-not-allowed ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white ring-2 ring-red-300 animate-pulse'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300'
            }`}
            title={isRecording ? 'Click to stop listening' : 'Click to speak'}
          >
            {isRecording ? (
              <>
                <span className="text-base leading-none">🔴</span>
                <span>Listening...</span>
              </>
            ) : (
              <>
                <span className="text-base leading-none">🎤</span>
                <span>Speak</span>
              </>
            )}
          </button>
        )}

        {/* INPUT FIELD (Shows transcribed text directly, editable by user) */}
        <div className="relative flex-1 flex items-center">
          <div className="absolute left-3.5 text-slate-400 pointer-events-none">
            <Terminal className="w-4 h-4" />
          </div>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isRecording}
            placeholder={
              scopedMachine
                ? `Describe fault for ${scopedMachine} or click Speak...`
                : "Describe the fault, click Speak, or enter an error code (e.g. E101)..."
            }
            className="w-full bg-slate-50 hover:bg-white focus:bg-white border border-slate-300 focus:border-slate-800 rounded-md py-2.5 pl-10 pr-28 text-sm md:text-base font-mono text-slate-900 placeholder:text-slate-400 placeholder:font-sans focus:outline-none focus:ring-1 focus:ring-slate-800 transition-all shadow-inner disabled:opacity-60"
          />

          {scopedMachine && (
            <div className="absolute right-2.5 flex items-center space-x-1 bg-slate-200 text-slate-800 px-2 py-0.5 rounded text-xs font-mono font-semibold">
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

        {/* BUTTON: ANALYZE (Submits query to existing pipeline) */}
        <button
          type="submit"
          disabled={disabled || !input.trim() || isRecording}
          className="bg-slate-900 hover:bg-black disabled:bg-slate-300 text-white px-5 py-2.5 rounded-md font-mono text-sm font-semibold flex items-center space-x-1.5 transition-colors shrink-0 shadow-xs cursor-pointer disabled:cursor-not-allowed"
          title="Analyze fault with existing diagnostic pipeline"
        >
          <span>Analyze</span>
        </button>

        {/* BUTTON: EDIT (Focuses input field for typing) */}
        <button
          type="button"
          onClick={handleEditClick}
          disabled={disabled || isRecording}
          className="px-4 py-2.5 border border-slate-300 hover:bg-slate-100 disabled:opacity-50 text-slate-700 rounded-md font-mono text-xs md:text-sm font-medium flex items-center space-x-1.5 transition-colors shrink-0 cursor-pointer disabled:cursor-not-allowed"
          title="Edit the query text in the input field"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Edit</span>
        </button>
      </form>

      {/* Sub-footer status bar */}
      <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1 pt-0.5">
        <div className="flex items-center space-x-4">
          <span>
            <strong className="text-slate-600 font-medium">RETURN</strong> to Analyze
          </span>
          <span>
            <strong className="text-slate-600 font-medium">ESC</strong> clear
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-emerald-600 font-medium text-[11px]">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>DIAGNOSTIC PIPELINE READY</span>
        </div>
      </div>
    </div>
  );
};
