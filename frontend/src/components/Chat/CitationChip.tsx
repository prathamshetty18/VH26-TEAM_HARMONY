import React from 'react';
import type { Citation } from '../../types';
import { FileText, ExternalLink } from 'lucide-react';

interface CitationChipProps {
  citation: Citation;
  onClickCitation?: (citation: Citation) => void;
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, onClickCitation }) => {
  return (
    <button
      type="button"
      onClick={() => onClickCitation && onClickCitation(citation)}
      className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-md bg-amber-50 hover:bg-amber-100 border border-amber-300 hover:border-amber-400 text-amber-900 text-xs md:text-sm font-mono transition-colors shadow-2xs group cursor-pointer"
      title="Click to view manual excerpt"
    >
      <FileText className="w-4 h-4 text-amber-700 shrink-0" />
      <span className="font-semibold text-amber-950 tracking-tight">
        {citation.manual}
      </span>
      <span className="text-amber-800 font-medium">
        p.{citation.page}
      </span>
      {citation.section && (
        <span className="hidden sm:inline text-amber-700/80 font-sans text-xs md:text-sm truncate max-w-[180px]">
          — {citation.section}
        </span>
      )}
      <ExternalLink className="w-3 h-3 text-amber-600 opacity-60 group-hover:opacity-100 transition-opacity ml-1" />
    </button>
  );
};
