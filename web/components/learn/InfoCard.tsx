'use client';

import { WallyAvatar } from '@/components/wally';
import type { InfoData } from '@/types/game';

interface InfoCardProps {
  data: InfoData;
  onContinue: () => void;
  className?: string;
}

export function InfoCard({ data, onContinue, className = '' }: InfoCardProps) {
  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Header with emoji */}
      <div className="text-center mb-6">
        <div
          className="inline-flex w-20 h-20 rounded-full items-center justify-center mb-3"
          style={{
            background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)',
            border: '2px solid rgba(0, 229, 204, 0.3)',
            boxShadow: '0 0 30px rgba(0, 229, 204, 0.2)',
          }}
        >
          <span className="text-5xl">{data.emoji || '📚'}</span>
        </div>
        <h2 className="text-xl font-bold text-white text-glow-cyan">{data.title}</h2>
      </div>

      {/* Content */}
      <div
        className="rounded-2xl p-5 mb-6"
        style={{
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(0, 229, 204, 0.05) 100%)',
          border: '1px solid rgba(168, 85, 247, 0.2)',
        }}
      >
        <p className="text-white/80 leading-relaxed">{data.content}</p>
      </div>

      {/* Wally's tip */}
      {data.wallyTip && (
        <div className="flex items-start gap-3 mb-6">
          <div className="flex-shrink-0">
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
                border: '2px solid rgba(250, 204, 21, 0.3)',
              }}
            >
              <WallyAvatar className="w-10 h-10" />
            </div>
          </div>
          <div
            className="flex-1 rounded-2xl rounded-tl-none p-4"
            style={{
              background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(251, 146, 60, 0.1) 100%)',
              border: '1px solid rgba(250, 204, 21, 0.3)',
            }}
          >
            <p className="text-sm">
              <span className="font-medium" style={{ color: '#FACC15' }}>Wally&apos;s Tip:</span>{' '}
              <span className="text-white/70">{data.wallyTip}</span>
            </p>
          </div>
        </div>
      )}

      {/* Continue button */}
      <button
        onClick={onContinue}
        className="w-full btn-wally py-3"
      >
        Got it! Continue
      </button>
    </div>
  );
}

export default InfoCard;
