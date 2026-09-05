import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  ExternalLink, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  AlertCircle,
  BookOpen
} from 'lucide-react';
import type { ManualItem } from '../../types';

interface PdfViewerProps {
  manual: ManualItem;
  initialPage?: number;
  baseUrl: string;
  onSwitchToText?: () => void;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({
  manual,
  initialPage = 1,
  baseUrl,
  onSwitchToText
}) => {
  const [currentPage, setCurrentPage] = useState<number>(initialPage);
  const [pageInput, setPageInput] = useState<string>(String(initialPage));
  const totalPages = manual.pages || 1;

  useEffect(() => {
    setCurrentPage(initialPage);
    setPageInput(String(initialPage));
  }, [initialPage, manual.filename]);

  const pdfUrl = manual.pdf_url 
    ? `${baseUrl}${manual.pdf_url}`
    : (manual.pdf_filename ? `${baseUrl}/api/manuals/${manual.pdf_filename}/pdf` : null);

  const iframeSrc = pdfUrl ? `${pdfUrl}?v=2#page=${currentPage}&toolbar=1&navpanes=0` : '';

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const next = currentPage - 1;
      setCurrentPage(next);
      setPageInput(String(next));
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      const next = currentPage + 1;
      setCurrentPage(next);
      setPageInput(String(next));
    }
  };

  const handlePageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseInt(pageInput, 10);
    if (!isNaN(p) && p >= 1 && p <= totalPages) {
      setCurrentPage(p);
    } else {
      setPageInput(String(currentPage));
    }
  };

  if (!pdfUrl || !manual.has_pdf) {
    return (
      <div className="h-[600px] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-200 rounded-2xl text-center">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 shadow-xs">
          <AlertCircle className="w-7 h-7" />
        </div>
        <h4 className="text-base font-bold text-slate-900 mb-1">No PDF Available for {manual.machine}</h4>
        <p className="text-xs text-slate-500 max-w-md mb-6 leading-relaxed">
          This manual is currently indexed as structured text. You can view the extracted chunks or upload an official PDF manual.
        </p>
        {onSwitchToText && (
          <button
            onClick={onSwitchToText}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all"
          >
            <FileText className="w-4 h-4" />
            <span>Switch to Structured Chunks</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[700px] bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-900 text-white text-xs border-b border-slate-800 gap-2">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <BookOpen className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-slate-200 truncate max-w-[240px] md:max-w-md">
            {manual.title}
          </span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono text-[10px]">
            PDF
          </span>
        </div>

        {/* Page navigation controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <form onSubmit={handlePageSubmit} className="flex items-center space-x-1">
            <span className="text-slate-400">Page</span>
            <input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              className="w-9 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-center font-mono text-white text-xs focus:outline-none focus:border-indigo-500"
            />
            <span className="text-slate-400">of {totalPages}</span>
          </form>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
            className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Action icons */}
        <div className="flex items-center space-x-2">
          {onSwitchToText && (
            <button
              onClick={onSwitchToText}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium text-[11px] transition-colors"
              title="View text chunks"
            >
              Text Mode
            </button>
          )}

          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Open in New Tab"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <a
            href={`${pdfUrl}?download=true`}
            download={manual.pdf_filename || `${manual.machine}.pdf`}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Download PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* PDF Viewport */}
      <div className="flex-1 w-full h-full bg-slate-100 relative">
        <iframe
          key={manual.filename}
          src={iframeSrc}
          title={manual.title}
          className="w-full h-full border-0"
        />
      </div>
    </div>
  );
};
