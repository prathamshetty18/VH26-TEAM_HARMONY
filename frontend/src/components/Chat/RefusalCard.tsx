import React from 'react';
import type { Message } from '../../types';
import { Info } from 'lucide-react';

interface RefusalCardProps {
  message: Message;
}

export const RefusalCard: React.FC<RefusalCardProps> = ({ message }) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs space-y-4 max-w-3xl">
      {/* Calm, neutral header - matching weight/calmness of normal card */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0">
          <Info className="w-5 h-5 text-slate-500" />
        </div>
        <div>
          <div className="text-xs md:text-sm font-mono uppercase tracking-wider text-slate-500 font-semibold">
            Information Boundary Notice
          </div>
          <p className="text-base md:text-lg font-semibold text-slate-800 mt-1">
            {message.refusalMessage || "The manuals don't cover this. I won't guess at a fix."}
          </p>
        </div>
      </div>


      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs md:text-sm text-slate-400 font-mono pl-11">
        <span>Verified retrieval gate: No matching manual chunks</span>
        <span>{message.timestamp}</span>
      </div>
    </div>
  );
};
