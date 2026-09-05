import React from 'react';
import type { Citation } from '../../types';
import { FileText, ExternalLink } from 'lucide-react';

interface CitationChipProps {
  citation: Citation;
  onClickCitation?: (citation: Citation) => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, onClickCitation }) => {
  const isKeyword = citation.match_type === 'keyword';
  const hasRerank = citation.rerank_score !== undefined && citation.rerank_score !== null && !isKeyword;

  return (
    <button
      type="button"
      onClick={() => onClickCitation && onClickCitation(citation)}
      className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-md bg-amber-50 hover:bg-amber-100 border border-amber-300 hover:border-amber-400 text-amber-900 text-xs md:text-sm font-mono transition-colors shadow-2xs group cursor-pointer"
      title={`Click to view manual excerpt (Rank #${citation.rank || 1}${hasRerank ? `, Cross-Encoder Score: ${citation.rerank_score}` : ''})`}
    >
      <FileText className="w-4 h-4 text-amber-700 shrink-0" />
      {citation.rank !== undefined && (
        <span className="bg-amber-200/80 text-amber-950 px-1.5 py-0.2 rounded text-[11px] font-bold">
          #{citation.rank}
        </span>
      )}
      <span className="font-semibold text-amber-950 tracking-tight">
        {citation.manual}
      </span>
      <span className="text-amber-800 font-medium">
        p.{citation.page}
      </span>
      {citation.section && (
        <span className="hidden sm:inline text-amber-700/80 font-sans text-xs md:text-sm truncate max-w-[170px]">
          — {citation.section}
        </span>
      )}
      {isKeyword && (
        <span className="text-[10px] bg-indigo-100 text-indigo-800 border border-indigo-200 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">
          Exact Code
        </span>
      )}
      {hasRerank && (
        <span className="text-[10px] bg-sky-100 text-sky-900 border border-sky-300 px-1.5 py-0.5 rounded font-semibold font-mono">
          Reranked ({citation.rerank_score! > 0 ? `+${citation.rerank_score}` : citation.rerank_score})
        </span>
      )}
      <ExternalLink className="w-3 h-3 text-amber-600 opacity-60 group-hover:opacity-100 transition-opacity ml-1" />
    </button>
  );
};
