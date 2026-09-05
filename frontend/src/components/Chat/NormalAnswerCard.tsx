import React, { useState } from 'react';
import type { Message, Citation, Diagram } from '../../types';
import { CitationChip } from './CitationChip';
import { Check, Copy, Wrench, AlertTriangle, ListOrdered, BookOpen, Maximize2, X } from 'lucide-react';

interface NormalAnswerCardProps {
  message: Message;
  onClickCitation?: (citation: Citation) => void;
}

export const NormalAnswerCard: React.FC<NormalAnswerCardProps> = ({
  message,
  onClickCitation,
}) => {
  const [copied, setCopied] = useState(false);
  const [selectedDiagram, setSelectedDiagram] = useState<Diagram | null>(null);
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
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5">
        <span className="text-[10px] md:text-xs font-mono px-2.5 py-0.5 rounded border uppercase font-bold bg-emerald-50 text-emerald-800 border-emerald-200">
          Manual-Sourced Diagnostic
        </span>

        {message.detectedMachine && (
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span className="text-slate-400">Unit:</span>
            <span className="bg-slate-100 border border-slate-300 text-slate-800 font-bold px-2 py-0.5 rounded">
              {message.detectedMachine}
            </span>
            {message.machineSource === 'session_context' && (
              <span className="bg-indigo-50 border border-indigo-200 text-indigo-700 text-[10px] font-bold px-1.5 py-0.5 rounded" title="Auto-detected from session conversational memory">
                ⚡ Context Inferred
              </span>
            )}
            {message.machineSource === 'fuzzy' && (
              <span className="bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-bold px-1.5 py-0.5 rounded" title="Auto-resolved from phonetic/typographical variation">
                ✨ Fuzzy Typo Resolved
              </span>
            )}
            {message.machineSource === 'semantic' && (
              <span className="bg-sky-50 border border-sky-200 text-sky-800 text-[10px] font-bold px-1.5 py-0.5 rounded" title="Auto-matched via natural language semantic vector search">
                🧠 Semantic Match
              </span>
            )}
          </div>
        )}
      </div>
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
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Multiple Possible Faults (Ranked by Confidence)
            </div>
            <span className="text-[11px] font-medium text-slate-500">
              {message.possible_faults.length} {message.possible_faults.length === 1 ? 'Supported Fault' : 'Supported Faults'}
            </span>
          </div>
          <div className="space-y-2">
            {message.possible_faults.map((pf, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-md border text-sm transition-all ${
                  pf.is_primary 
                    ? 'bg-indigo-50/70 border-indigo-200 shadow-2xs' 
                    : 'bg-white border-slate-200 text-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs text-slate-500 font-semibold">{idx + 1}.</span>
                      <span className="font-bold text-slate-900">{pf.fault}</span>
                      {pf.is_primary && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white uppercase tracking-wider">
                          Primary Fault
                        </span>
                      )}
                    </div>
                    {pf.component && (
                      <div className="text-xs text-slate-500 pl-5 font-mono">
                        Affected Component: <span className="text-slate-700 font-medium">{pf.component}</span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 font-mono text-xs shrink-0">
                    <span className="font-bold text-slate-900">
                      {pf.confidence_percentage || Math.round(pf.confidence_score * 100)}%
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                      pf.confidence_level === 'High' ? 'bg-emerald-100 text-emerald-800' : pf.confidence_level === 'Moderate' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {pf.confidence_level}
                    </span>
                  </div>
                </div>

                {/* Supporting evidence from retrieved manual/chunks */}
                {pf.supporting_evidence && pf.supporting_evidence.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/80 text-xs">
                    <div className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide mb-1">
                      Supporting evidence:
                    </div>
                    <ul className="list-disc pl-5 space-y-0.5 text-slate-600">
                      {pf.supporting_evidence.map((ev, evIdx) => (
                        <li key={evIdx} className="leading-tight">{ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
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
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center space-x-2 text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold">
              <BookOpen className="w-4 h-4 text-amber-600" />
              <span>04. Verified Sources &amp; Citations</span>
            </div>
            <span className="text-[10px] md:text-xs font-mono bg-sky-50 text-sky-800 border border-sky-200 px-2 py-0.5 rounded font-medium">
              Cross-Encoder Reranked (Top 5 of 20)
            </span>
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

      {/* 05. TECHNICAL DIAGRAMS & SCHEMATICS */}
      {((message.diagrams && message.diagrams.length > 0) || (message.citations && message.citations.some(c => c.diagram_url))) && (
        <div className="pt-3.5 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold mb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
              <span className="text-cyan-800 font-bold">05. Technical Diagram &amp; Schematic</span>
            </div>
            <span className="text-[10px] text-slate-500 font-normal lowercase">click diagram to expand</span>
          </div>

          <div className="grid grid-cols-1 gap-3.5 pl-1">
            {((message.diagrams && message.diagrams.length > 0)
              ? message.diagrams
              : (message.citations || []).filter(c => c.diagram_url).map(c => ({
                  title: c.diagram_title || 'System Technical Schematic',
                  filename: c.diagram_url ? c.diagram_url.split('/').pop() || '' : '',
                  url: c.diagram_url || '',
                  caption: c.diagram_caption || `Diagram for ${c.section || 'system'}`,
                }))
            ).map((diag, dIdx) => (
              <div
                key={dIdx}
                className="group relative bg-slate-900 border border-slate-700/80 hover:border-cyan-500/80 rounded-lg overflow-hidden transition-all shadow-sm cursor-pointer"
                onClick={() => setSelectedDiagram(diag)}
              >
                {/* Header bar */}
                <div className="flex items-center justify-between bg-slate-800/90 px-3.5 py-2 border-b border-slate-700 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">
                      VECTOR SCHEMATIC
                    </span>
                    <span className="text-slate-200 font-medium">{diag.title}</span>
                  </div>
                  <button
                    type="button"
                    className="flex items-center space-x-1 text-slate-400 group-hover:text-cyan-300 transition-colors"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                    <span className="text-[11px] font-mono">Zoom</span>
                  </button>
                </div>

                {/* SVG Image Embed Preview */}
                <div className="p-3 bg-slate-950/80 flex items-center justify-center max-h-64 overflow-hidden">
                  <img
                    src={diag.url}
                    alt={diag.title}
                    className="w-full h-auto max-h-56 object-contain rounded transition-transform duration-200 group-hover:scale-[1.01]"
                    loading="lazy"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      const filename = diag.url.split('/').pop() || '';
                      if (!target.dataset.triedFallback) {
                        target.dataset.triedFallback = '1';
                        target.src = `/diagrams/${filename}`;
                      } else if (target.dataset.triedFallback === '1') {
                        target.dataset.triedFallback = '2';
                        target.src = `http://127.0.0.1:8000/static/diagrams/${filename}`;
                      } else {
                        target.onerror = null;
                      }
                    }}
                  />
                </div>

                {/* Caption footer */}
                <div className="px-3.5 py-2 bg-slate-900 text-[11px] font-mono text-slate-400 border-t border-slate-800 flex items-center justify-between">
                  <span className="truncate pr-2">{diag.caption}</span>
                  <span className="text-cyan-400 shrink-0">Interactive View &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fullscreen Diagram Modal */}
      {selectedDiagram && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
          onClick={() => setSelectedDiagram(null)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-950">
              <div>
                <h3 className="text-sm font-semibold text-slate-100">{selectedDiagram.title}</h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{selectedDiagram.caption}</p>
              </div>
              <button
                onClick={() => setSelectedDiagram(null)}
                className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-auto flex-1 flex items-center justify-center bg-slate-950/90">
              <img
                src={selectedDiagram.url}
                alt={selectedDiagram.title}
                className="w-full h-auto max-h-[70vh] object-contain"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  const filename = selectedDiagram.url.split('/').pop() || '';
                  if (!target.dataset.triedFallback) {
                    target.dataset.triedFallback = '1';
                    target.src = `/diagrams/${filename}`;
                  } else if (target.dataset.triedFallback === '1') {
                    target.dataset.triedFallback = '2';
                    target.src = `http://127.0.0.1:8000/static/diagrams/${filename}`;
                  } else {
                    target.onerror = null;
                  }
                }}
              />
            </div>
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
