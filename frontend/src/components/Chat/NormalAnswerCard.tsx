import React, { useState } from 'react';
import type { Message, Citation } from '../../types';
import { CitationChip } from './CitationChip';
import { Check, Copy, Wrench, AlertTriangle, ListOrdered, BookOpen } from 'lucide-react';

interface NormalAnswerCardProps {
  message: Message;
  onClickCitation?: (citation: Citation) => void;
}

export const NormalAnswerCard: React.FC<NormalAnswerCardProps> = ({
  message,
  onClickCitation,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const textToCopy = `Meaning: ${message.meaning || ''}\n\nCauses:\n${(message.causes || []).map((c) => `- ${c}`).join('\n')}\n\nCorrective Steps:\n${(message.steps || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}\n\nSources:\n${(message.citations || []).map((c) => `${c.manual}, p.${c.page}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-5 max-w-3xl">
      {/* 01. MEANING */}
      {message.meaning && (
        <div>
          <div className="flex items-center space-x-2 text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold mb-1.5">
            <Wrench className="w-4 h-4 text-slate-500" />
            <span>01. Fault Diagnostic & Meaning</span>
          </div>
          <p className="text-base md:text-lg text-slate-900 leading-relaxed pl-6 font-normal">
            {message.meaning}
          </p>
        </div>
      )}

      {/* 02. PROBABLE CAUSES */}
      {message.causes && message.causes.length > 0 && (
        <div className="pt-3 border-t border-slate-100">
          <div className="flex items-center space-x-2 text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2">
            <AlertTriangle className="w-4 h-4 text-slate-500" />
            <span>02. Probable Causes</span>
          </div>
          <ul className="space-y-2 pl-6 text-sm md:text-base text-slate-800">
            {message.causes.map((cause, idx) => (
              <li key={idx} className="flex items-start space-x-2.5">
                <span className="w-2 h-2 rounded-full bg-slate-400 mt-2 shrink-0" />
                <span className="leading-normal">{cause}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 03. CORRECTIVE STEPS */}
      {message.steps && message.steps.length > 0 && (
        <div className="pt-3 border-t border-slate-100">
          <div className="flex items-center space-x-2 text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2.5">
            <ListOrdered className="w-4 h-4 text-slate-500" />
            <span>03. Corrective Action Steps</span>
          </div>
          <ol className="space-y-2.5 pl-1">
            {message.steps.map((step, idx) => (
              <li key={idx} className="flex items-start space-x-3.5 text-sm md:text-base text-slate-900 bg-slate-50/70 border border-slate-200/80 rounded-md p-3">
                <span className="w-6 h-6 rounded bg-slate-200 text-slate-800 font-mono text-sm font-bold flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed font-mono-code text-sm md:text-base text-slate-800">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* 04. SOURCES / CITATIONS */}
      {message.citations && message.citations.length > 0 && (
        <div className="pt-3.5 border-t border-slate-100">
          <div className="flex items-center space-x-2 text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2.5">
            <BookOpen className="w-4 h-4 text-amber-600" />
            <span>04. Verified Sources</span>
          </div>
          <div className="flex flex-wrap gap-2.5 pl-1">
            {message.citations.map((citation, idx) => (
              <CitationChip
                key={idx}
                citation={citation}
                onClickCitation={onClickCitation}
              />
            ))}
          </div>
        </div>
      )}

      {/* Footer action bar */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs md:text-sm text-slate-400 font-mono">
        <span>{message.timestamp}</span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded transition-colors text-xs md:text-sm cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Steps</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
