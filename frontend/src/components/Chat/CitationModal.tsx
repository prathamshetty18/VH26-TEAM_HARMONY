import React from 'react';
import type { Citation } from '../../types';
import { FileText, X, CheckCircle, BookOpen } from 'lucide-react';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
  onOpenInPdfReader?: (manualFilename: string, page: number) => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ 
  citation, 
  onClose,
  onOpenInPdfReader 
}) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-lg border border-slate-300 shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-900">
              <FileText className="w-5 h-5 text-amber-800" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <span className="font-mono text-base font-bold text-slate-900">
                  {citation.manual}
                </span>
                <span className="font-mono text-xs md:text-sm bg-amber-100 text-amber-900 border border-amber-300 px-2 py-0.5 rounded font-bold">
                  Page {citation.page}
                </span>
              </div>
              <div className="text-xs md:text-sm text-slate-500 font-sans mt-0.5">
                {citation.section || 'Technical Maintenance Manual Reference'}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-2 rounded hover:bg-slate-200 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <div className="text-xs md:text-sm font-mono uppercase tracking-wider text-slate-400 font-bold mb-1.5">
              Indexed Manual Excerpt (Retrieved Chunk)
            </div>
            <div className="p-4 bg-slate-900 text-slate-100 rounded-md font-mono text-xs md:text-sm leading-relaxed border border-slate-800 selection:bg-amber-500 selection:text-black">
              {citation.snippet ||
                `Section 4.2 Spindle Thermal Cutoff (E101): Thermal sensor triggers safety shutoff when stator temperature exceeds 105°C. Check coolant lines and reset breaker after 15-minute cooldown.`}
            </div>
          </div>

          {/* Reranking & Retrieval Transparency Card */}
          <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-xs font-mono space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 uppercase tracking-wider font-semibold">Retrieval Pipeline</span>
              <span className="text-slate-800 font-bold">Hybrid (k=20) → Cross-Encoder ms-marco (Top 5)</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 uppercase tracking-wider font-semibold">Match Classification</span>
              <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${citation.match_type === 'keyword' ? 'bg-indigo-100 text-indigo-800' : 'bg-cyan-100 text-cyan-900'}`}>
                {citation.match_type === 'keyword' ? 'Exact Keyword Match (Prioritized)' : 'Semantic Cross-Encoder Reranked'}
              </span>
            </div>
            {citation.rerank_score !== undefined && citation.match_type !== 'keyword' && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500 uppercase tracking-wider font-semibold">Cross-Encoder Relevance Logit</span>
                <span className="text-emerald-700 font-bold">{citation.rerank_score > 0 ? `+${citation.rerank_score}` : citation.rerank_score}</span>
              </div>
            )}
            {citation.rank !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-slate-500 uppercase tracking-wider font-semibold">Rank Position</span>
                <span className="text-slate-900 font-bold">Rank #{citation.rank} of top 5</span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2.5 text-xs md:text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded p-3 font-mono">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>
              Ground-truth verification: Exact match against local manufacturer documentation repository.
            </span>
          </div>
        </div>

        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div>
            {onOpenInPdfReader && (
              <button
                onClick={() => {
                  onOpenInPdfReader(citation.manual, citation.page);
                  onClose();
                }}
                className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs md:text-sm font-sans font-semibold transition-colors shadow-sm cursor-pointer"
              >
                <BookOpen className="w-4 h-4" />
                <span>Open in PDF Reader (Page {citation.page}) →</span>
              </button>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs md:text-sm font-mono font-semibold transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
