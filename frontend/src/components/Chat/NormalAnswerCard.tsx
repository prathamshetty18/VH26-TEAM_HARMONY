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
  const [showExplanation, setShowExplanation] = useState(false);

  const handleCopy = () => {
    const textToCopy = `Fault: ${message.fault || 'Hardware Fault'}\nConfidence: ${message.confidence_percentage || Math.round((message.confidence_score || 0)*100)}% (${message.confidence_level || 'Moderate'})\nMeaning: ${message.meaning || ''}\n\nCauses:\n${(message.causes || []).map((c) => `- ${c}`).join('\n')}\n\nCorrective Steps:\n${(message.steps || []).map((s, i) => `${i + 1}. ${s}`).join('\n')}\n\nSources:\n${(message.citations || []).map((c) => `${c.manual}, p.${c.page}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasConfidence = message.confidence_score !== undefined && message.confidence_score !== null;
  const pct = message.confidence_percentage !== undefined ? message.confidence_percentage : (hasConfidence ? Math.round((message.confidence_score || 0) * 100) : 0);
  const lvl = message.confidence_level || (pct >= 90 ? 'High' : pct >= 70 ? 'Moderate' : 'Low');

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-5 max-w-3xl">
      {/* FAULT DETECTED BANNER */}
      {message.fault && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-4 rounded-lg border border-indigo-900/50 shadow-sm">
          <div className="flex items-center space-x-2 mb-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-red-500/20 text-red-300 border border-red-500/30">
              <span className="w-2 h-2 rounded-full bg-red-500 mr-1.5 animate-pulse" />
              FAULT DETECTED
            </span>
            {message.component && (
              <span className="text-xs text-indigo-300 font-mono">
                • {message.component}
              </span>
            )}
          </div>
          <h3 className="text-lg md:text-xl font-bold text-white tracking-tight">
            {message.fault}
          </h3>
        </div>
      )}

      {/* AI CONFIDENCE ASSESSMENT */}
      {hasConfidence && (
        <div className="bg-slate-50/80 border border-slate-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-0.5">
                AI Confidence
              </div>
              <div className="flex items-baseline space-x-3">
                <span className={`text-2xl md:text-3xl font-extrabold font-mono ${lvl === 'High' ? 'text-emerald-600' : lvl === 'Moderate' ? 'text-amber-600' : 'text-slate-600'}`}>
                  {pct}%
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide border ${
                  lvl === 'High' 
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                    : lvl === 'Moderate'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}>
                  Confidence Level: {lvl}
                </span>
              </div>
            </div>
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-md bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 transition-colors shadow-2xs cursor-pointer"
            >
              <span>{showExplanation ? 'Hide Explanation' : 'View Explanation'}</span>
            </button>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                lvl === 'High' ? 'bg-emerald-500' : lvl === 'Moderate' ? 'bg-amber-500' : 'bg-slate-500'
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>

          <div className="flex justify-between text-xs text-slate-400 font-mono">
            <span>&lt;70% Low</span>
            <span>70–89% Moderate</span>
            <span>90–100% High</span>
          </div>

          {/* Non-guarantee disclaimer */}
          <div className="bg-white/80 border border-dashed border-slate-300 rounded p-2.5 text-xs text-slate-600 flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="leading-normal">
              <strong>Non-Guarantee Notice:</strong> The confidence score is presented as the AI model's predictive confidence and does not guarantee that the fault is physically present. Field verification is required.
            </p>
          </div>

          {/* Explanation Drawer */}
          {showExplanation && (
            <div className="mt-3 pt-3 border-t border-slate-200 space-y-2 text-xs text-slate-700 animate-in fade-in duration-200">
              <div className="font-bold text-indigo-950 uppercase tracking-wider">
                Why the AI Assigned This Score:
              </div>
              <p className="bg-white p-2.5 rounded border border-indigo-100 text-slate-800 leading-relaxed">
                {message.evidence?.reasoning || `The system detected a ${pct}% alignment with technical manual specifications and matching telemetry symptom patterns.`}
              </p>
              {message.evidence?.sensor_readings && (
                <div>
                  <div className="font-semibold text-slate-600 mb-1">Contributing Sensor Readings:</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 font-mono text-xs">
                    {Object.entries(message.evidence.sensor_readings).map(([key, val]) => (
                      <div key={key} className="bg-white p-2 rounded border border-slate-200">
                        <span className="text-slate-500 uppercase tracking-tight block text-[10px]">{key.replace(/_/g, ' ')}</span>
                        <span className="font-semibold text-slate-900">{String(val)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* MULTIPLE POSSIBLE FAULTS (RANKED BY CONFIDENCE) */}
      {message.possible_faults && message.possible_faults.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Multiple Possible Faults (Ranked by Confidence)
          </div>
          <div className="space-y-1.5">
            {message.possible_faults.map((pf, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-2.5 rounded-md border text-sm ${
                  pf.is_primary 
                    ? 'bg-indigo-50/70 border-indigo-200 font-semibold' 
                    : 'bg-white border-slate-200 text-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs text-slate-500 w-4">{idx + 1}.</span>
                  <span>{pf.fault}</span>
                  {pf.is_primary && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white uppercase tracking-wider">
                      Primary
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2 font-mono text-xs">
                  <span className="font-bold">{pf.confidence_percentage || Math.round(pf.confidence_score * 100)}%</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                    pf.confidence_level === 'High' ? 'bg-emerald-100 text-emerald-800' : pf.confidence_level === 'Moderate' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'
                  }`}>
                    {pf.confidence_level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
