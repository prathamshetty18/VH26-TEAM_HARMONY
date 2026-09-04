import React, { useEffect, useRef } from 'react';
import type { Message, Citation, AmbiguityOption } from '../../types';
import { NormalAnswerCard } from './NormalAnswerCard';
import { AmbiguityCard } from './AmbiguityCard';
import { RefusalCard } from './RefusalCard';
import { User, Cpu, Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  onClickCitation: (citation: Citation) => void;
  onSelectAmbiguityOption: (option: AmbiguityOption) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  onClickCitation,
  onSelectAmbiguityOption,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
          <div className="w-14 h-14 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center mb-3.5">
            <Cpu className="w-7 h-7 text-slate-500" />
          </div>
          <h3 className="font-mono text-base font-bold text-slate-800 uppercase tracking-wider">
            MachineAssist Diagnostic HMI
          </h3>
          <p className="text-sm text-slate-500 max-w-lg mt-1.5 leading-relaxed">
            Manuals indexed. Ask about an error code or symptom.
          </p>
        </div>
      ) : (
        messages.map((message) => {
          if (message.role === 'user') {
            return (
              <div key={message.id} className="flex justify-end">
                <div className="max-w-2xl bg-slate-900 text-white rounded-lg px-5 py-3.5 shadow-xs space-y-1.5">
                  <div className="flex items-center justify-between space-x-3 text-xs font-mono text-slate-400 border-b border-slate-800 pb-1.5 mb-1">
                    <span className="flex items-center space-x-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-semibold tracking-wider">TECHNICIAN QUERY</span>
                    </span>
                    <span>{message.timestamp}</span>
                  </div>
                  <p className="text-base font-sans leading-relaxed text-slate-100">
                    {message.content}
                  </p>
                </div>
              </div>
            );
          }

          return (
            <div key={message.id} className="flex justify-start">
              <div className="w-full">
                {message.cardType === 'normal' && (
                  <NormalAnswerCard
                    message={message}
                    onClickCitation={onClickCitation}
                  />
                )}
                {message.cardType === 'ambiguity' && (
                  <AmbiguityCard
                    message={message}
                    onSelectOption={onSelectAmbiguityOption}
                  />
                )}
                {message.cardType === 'refusal' && (
                  <RefusalCard message={message} />
                )}
              </div>
            </div>
          );
        })
      )}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs flex items-center space-x-3 text-sm font-mono text-slate-700">
            <Loader2 className="w-5 h-5 animate-spin text-slate-700" />
            <span className="font-semibold">RETRIEVING & VERIFYING TECHNICAL MANUAL CHUNKS...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
