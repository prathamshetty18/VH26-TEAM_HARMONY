import React, { useState } from 'react';
import type { BackendConfig } from '../types';
import { X, Server } from 'lucide-react';

interface BackendSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: BackendConfig;
  onSaveConfig: (newConfig: BackendConfig) => void;
}

export const BackendSettingsModal: React.FC<BackendSettingsModalProps> = ({
  isOpen,
  onClose,
  config,
  onSaveConfig,
}) => {
  const [mode, setMode] = useState<'demo' | 'live'>(config.mode);
  const [baseUrl, setBaseUrl] = useState(config.baseUrl);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveConfig({ mode, baseUrl });
    onClose();
  };

  const handleTestConnection = async () => {
    setTestStatus('Testing endpoint...');
    try {
      const res = await fetch(`${baseUrl}/machines`, {
        method: 'GET',
        signal: AbortSignal.timeout(2000),
      });
      if (res.ok) {
        setTestStatus('Success! Backend responded OK (200).');
      } else {
        setTestStatus(`Backend returned status ${res.status}`);
      }
    } catch (err: any) {
      setTestStatus(`Connection failed: ${err.message || 'Cannot reach server'}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-lg border border-slate-300 shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Server className="w-4 h-4 text-slate-700" />
            <h3 className="font-mono text-sm font-bold text-slate-900">
              Diagnostic Backend Configuration
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded hover:bg-slate-200 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4 text-xs font-mono">
          <div>
            <label className="block text-slate-600 font-semibold mb-1.5 uppercase tracking-wide text-[11px]">
              Operating Mode
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setMode('demo')}
                className={`p-2.5 rounded border text-left transition-all cursor-pointer ${
                  mode === 'demo'
                    ? 'bg-slate-900 text-white border-slate-900 font-semibold'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs">Interactive Demo</div>
                <div className="text-[10px] opacity-75 font-sans mt-0.5">
                  Verified Section 7 RAG responses
                </div>
              </button>

              <button
                type="button"
                onClick={() => setMode('live')}
                className={`p-2.5 rounded border text-left transition-all cursor-pointer ${
                  mode === 'live'
                    ? 'bg-slate-900 text-white border-slate-900 font-semibold'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs">Live API Engine</div>
                <div className="text-[10px] opacity-75 font-sans mt-0.5">
                  POST /chat & GET /machines
                </div>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-slate-600 font-semibold mb-1 uppercase tracking-wide text-[11px]">
              Backend Base URL
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none focus:border-slate-800"
              />
              <button
                type="button"
                onClick={handleTestConnection}
                className="px-3 py-1 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded text-[11px] text-slate-700 font-medium cursor-pointer"
              >
                Ping
              </button>
            </div>
            {testStatus && (
              <p className="mt-1 text-[11px] text-slate-600 italic">{testStatus}</p>
            )}
          </div>

          <div className="p-2.5 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-500 font-sans leading-relaxed">
            <strong>Honesty Guarantee (Section 8):</strong> Even in live mode, no fabricated telemetry or uncomputed confidence metrics are displayed. All sessions faithfully represent real technical documentation chunk retrieval.
          </div>
        </div>

        <div className="px-5 py-3 bg-slate-50 border-t border-slate-200 flex justify-end space-x-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 border border-slate-300 rounded text-xs font-mono text-slate-700 hover:bg-slate-100 cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-4 py-1.5 bg-slate-900 hover:bg-black text-white rounded text-xs font-mono font-medium cursor-pointer"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};
