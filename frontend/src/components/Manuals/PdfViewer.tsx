import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  ExternalLink, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  AlertCircle,
  BookOpen,
  Loader2
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
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const totalPages = manual.pages || 1;

  useEffect(() => {
    setCurrentPage(initialPage);
    setPageInput(String(initialPage));
  }, [initialPage, manual.filename]);

  // If in Vite dev server (port 5173), prefer same-origin proxy to eliminate any cross-origin framing issues
  const isViteDev = typeof window !== 'undefined' && window.location.port === '5173';
  const resolvedBaseUrl = isViteDev ? '' : (baseUrl || '');

  const pdfEndpoint = manual.pdf_url 
    ? manual.pdf_url 
    : (manual.pdf_filename ? `/api/manuals/${manual.pdf_filename}/pdf` : null);

  const directPdfUrl = pdfEndpoint 
    ? (pdfEndpoint.startsWith('http') ? pdfEndpoint : `${resolvedBaseUrl}${pdfEndpoint}`)
    : null;

  // Fetch as blob for 100% same-origin embedding and reliable plugin initialization
  useEffect(() => {
    if (!directPdfUrl || !manual.has_pdf) {
      setIsLoading(false);
      setBlobUrl(null);
      return;
    }

    let active = true;
    setIsLoading(true);

    fetch(directPdfUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        if (!active) return;
        const url = URL.createObjectURL(blob);
        setBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
        setIsLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        console.warn('[PdfViewer] Blob load failed, using direct URL fallback:', err);
        setBlobUrl(null);
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [directPdfUrl, manual.has_pdf]);

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

  if (!directPdfUrl || !manual.has_pdf) {
    return (
      <div className="h-[650px] flex flex-col items-center justify-center p-8 bg-slate-50 border border-slate-200 rounded-2xl text-center">
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
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer"
          >
            <FileText className="w-4 h-4" />
            <span>Switch to Structured Chunks</span>
          </button>
        )}
      </div>
    );
  }

  // Active rendering URL: prioritize blob URL, fallback to direct URL
  const activePdfSource = blobUrl || directPdfUrl;
  const embeddedViewUrl = `${activePdfSource}#page=${currentPage}&toolbar=1&navpanes=0`;

  return (
    <div className="flex flex-col h-[750px] bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
      {/* Top Toolbar */}
      <div className="shrink-0 flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-900 text-white text-xs border-b border-slate-800 gap-2 z-20">
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
            className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
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
              className="w-10 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-center font-mono text-white text-xs focus:outline-none focus:border-indigo-500"
            />
            <span className="text-slate-400">of {totalPages}</span>
          </form>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
            className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
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
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-medium text-[11px] transition-colors cursor-pointer"
              title="View text chunks"
            >
              Text Mode
            </button>
          )}

          <a
            href={directPdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Open in New Tab"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <a
            href={`${directPdfUrl}?download=true`}
            download={manual.pdf_filename || `${manual.machine}.pdf`}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Download PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* PDF Viewport */}
      <div className="flex-1 w-full min-h-0 relative bg-slate-100 overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 z-10 bg-slate-100/80 backdrop-blur-xs flex flex-col items-center justify-center text-slate-700">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-2" />
            <span className="text-xs font-semibold text-slate-600">Loading technical manual PDF...</span>
          </div>
        )}

        <object
          key={`${manual.filename}_p${currentPage}_${blobUrl ? 'blob' : 'direct'}`}
          data={embeddedViewUrl}
          type="application/pdf"
          className="w-full h-full block"
        >
          <iframe
            src={embeddedViewUrl}
            title={manual.title}
            className="w-full h-full border-0 block"
          >
            <div className="h-full flex flex-col items-center justify-center p-8 bg-slate-50 text-center">
              <BookOpen className="w-10 h-10 text-indigo-600 mb-3" />
              <h4 className="text-sm font-bold text-slate-900 mb-1">Embedded Viewer Standby</h4>
              <p className="text-xs text-slate-500 max-w-sm mb-4">
                Your browser preferences require opening PDF files in a dedicated window.
              </p>
              <div className="flex items-center space-x-2">
                <a
                  href={directPdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-all"
                >
                  Open PDF in New Window ↗
                </a>
                <a
                  href={`${directPdfUrl}?download=true`}
                  download={manual.pdf_filename || `${manual.machine}.pdf`}
                  className="px-4 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold transition-all"
                >
                  Download File
                </a>
              </div>
            </div>
          </iframe>
        </object>
      </div>
    </div>
  );
};
