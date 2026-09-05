import React, { useState, useRef } from 'react';
import { 
  X, 
  UploadCloud, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Loader2, 
  Sparkles,
  ShieldCheck,
  Check
} from 'lucide-react';

interface PdfUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  baseUrl: string;
  onUploadSuccess: () => void;
}

export const PdfUploadModal: React.FC<PdfUploadModalProps> = ({
  isOpen,
  onClose,
  baseUrl,
  onUploadSuccess
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  
  // Review Studio State
  const [isReviewing, setIsReviewing] = useState<boolean>(false);
  const [draftContent, setDraftContent] = useState<string>('');
  const [draftMachine, setDraftMachine] = useState<string>('');
  const [chunkCount, setChunkCount] = useState<number>(0);
  const [sourceLanguage, setSourceLanguage] = useState<string>('English');
  const [isTranslated, setIsTranslated] = useState<boolean>(false);
  const [isConfirming, setIsConfirming] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      selectFile(e.dataTransfer.files[0]);
    }
  };

  const selectFile = (f: File) => {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'txt') {
      setError('Only .pdf and .txt factory manual files are supported.');
      return;
    }
    setFile(f);
    setError(null);
    setSuccessMessage(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setStatusMessage(file.name.endsWith('.pdf') 
      ? 'Extracting PDF pages with pypdf and structuring via Gemini 2.5 Flash...' 
      : 'Validating manual specification...'
    );

    const formData = new FormData();
    formData.append('file', file);

    try {
      const resp = await fetch(`${baseUrl}/manuals/upload`, {
        method: 'POST',
        body: formData
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      if (data.status === 'needs_review') {
        setIsReviewing(true);
        setDraftContent(data.draft_text || '');
        setDraftMachine(data.machine || file.name.replace(/\.[^/.]+$/, ''));
        setChunkCount(data.chunk_count || 0);
        setSourceLanguage(data.detected_language || 'English');
        setIsTranslated(!!data.is_translated);
      } else if (data.status === 'success') {
        setSuccessMessage(`Successfully indexed ${data.machine || 'manual'} with ${data.chunk_count} verified chunks!`);
        onUploadSuccess();
        setTimeout(() => {
          handleReset();
          onClose();
        }, 1500);
      }
    } catch (err: any) {
      setError(err.message || 'Error processing manual');
    } finally {
      setIsUploading(false);
      setStatusMessage('');
    }
  };

  const handleConfirm = async () => {
    if (!draftContent.trim() || !draftMachine.trim()) return;

    setIsConfirming(true);
    setError(null);

    try {
      const resp = await fetch(`${baseUrl}/manuals/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine: draftMachine,
          content: draftContent
        })
      });

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.detail || 'Failed to confirm manual');
      }

      setSuccessMessage(`Manual confirmed and indexed! ${data.chunk_count} chunks live in ChromaDB.`);
      onUploadSuccess();
      setTimeout(() => {
        handleReset();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Confirmation failed');
    } finally {
      setIsConfirming(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setIsReviewing(false);
    setDraftContent('');
    setDraftMachine('');
    setChunkCount(0);
    setError(null);
    setSuccessMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className={`bg-white rounded-3xl border border-slate-200 shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ${
          isReviewing ? 'w-full max-w-4xl max-h-[85vh]' : 'w-full max-w-lg'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
              <UploadCloud className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {isReviewing ? 'Review & Confirm Manual Ingestion' : 'Upload Technical Manual'}
              </h3>
              <p className="text-xs text-slate-500">
                {isReviewing 
                  ? 'Verify AI structured manual excerpt before writing to ChromaDB vector store' 
                  : 'Ingest factory manuals in PDF or TXT format'
                }
              </p>
            </div>
          </div>
          <button
            onClick={() => { handleReset(); onClose(); }}
            className="p-1.5 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {error && (
            <div className="mb-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Validation Error: </span>
                {error}
              </div>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="font-semibold">{successMessage}</span>
            </div>
          )}

          {!isReviewing ? (
            /* Upload Screen */
            <div className="space-y-4">
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                  file 
                    ? 'border-indigo-600 bg-indigo-50/30' 
                    : 'border-slate-300 hover:border-indigo-400 bg-slate-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && selectFile(e.target.files[0])}
                />
                <div className="w-12 h-12 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-center mx-auto mb-3 text-indigo-600">
                  {file ? <FileText className="w-6 h-6" /> : <UploadCloud className="w-6 h-6" />}
                </div>
                {file ? (
                  <div>
                    <div className="font-bold text-sm text-slate-900">{file.name}</div>
                    <div className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(1)} KB • Click to change</div>
                  </div>
                ) : (
                  <div>
                    <div className="font-bold text-sm text-slate-800">Click or drag & drop factory manual</div>
                    <div className="text-xs text-slate-500 mt-1">Supports PDF technical documents (.pdf) & delimited text (.txt)</div>
                  </div>
                )}
              </div>

              {/* Feature Callout */}
              <div className="bg-slate-50 rounded-2xl p-3.5 border border-slate-200 text-xs space-y-1.5 text-slate-600">
                <div className="flex items-center space-x-2 font-semibold text-slate-900">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Two-Tier PDF Pipeline with Gemini AI</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  PDF manuals are automatically parsed page-by-page, structured into standard <code className="text-indigo-600 font-mono">SECTION:</code> blocks while preserving exact numeric tolerances, and staged for your review before indexing.
                </p>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  onClick={() => { handleReset(); onClose(); }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all flex items-center space-x-2"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>{statusMessage || 'Processing...'}</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Process & Ingest Manual</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* Human-in-the-Loop Review Studio */
            <div className="space-y-4">
              {isTranslated && (
                <div className="p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="px-2.5 py-1 rounded-lg bg-amber-200 text-amber-950 font-bold text-[10px] uppercase tracking-wider">
                      {sourceLanguage} → English
                    </span>
                    <span className="font-medium text-amber-900">
                      Document translated to canonical English for RAG retrieval. Verify technical parameters below.
                    </span>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Machine Identifier
                  </label>
                  <input
                    type="text"
                    value={draftMachine}
                    onChange={(e) => setDraftMachine(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 font-medium text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Verified Chunks Extracted
                  </label>
                  <div className="px-3 py-2 rounded-xl border border-slate-200 bg-emerald-50/50 text-emerald-800 font-semibold text-xs flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>{chunkCount} valid sections formatted for vector indexing</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Structured Specification Preview & Corrections
                  </label>
                  <span className="text-[11px] text-slate-400 font-mono">MANUAL_FORMAT_SPEC.md</span>
                </div>
                <textarea
                  value={draftContent}
                  onChange={(e) => setDraftContent(e.target.value)}
                  rows={14}
                  className="w-full p-4 rounded-2xl border border-slate-200 bg-slate-900 text-slate-200 font-mono text-xs focus:outline-none focus:border-indigo-500 leading-relaxed resize-none shadow-inner"
                />
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <button
                  onClick={() => setIsReviewing(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  ← Back to Upload
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={isConfirming}
                  className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-emerald-500/20 transition-all flex items-center space-x-2"
                >
                  {isConfirming ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Writing to ChromaDB...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Approve & Index into Vector DB</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
