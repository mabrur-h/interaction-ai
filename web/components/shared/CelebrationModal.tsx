'use client';

import { useEffect, useState } from 'react';
import { WallyAvatar } from '@/components/wally';

interface CelebrationModalProps {
  isOpen: boolean;
  xpEarned: number;
  coinsEarned?: number;
  message?: string;
  onClose: () => void;
}

export function CelebrationModal({
  isOpen,
  xpEarned,
  coinsEarned = 0,
  message = 'Great job!',
  onClose,
}: CelebrationModalProps) {
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const confettiColors = ['#00E5CC', '#A855F7', '#F472B6', '#FACC15', '#4ADE80', '#FF6B6B'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop with blur */}
      <div
        className="absolute inset-0"
        style={{
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(8px)',
        }}
        onClick={onClose}
      />

      {/* Confetti */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(60)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 0.5}s`,
                backgroundColor: confettiColors[Math.floor(Math.random() * confettiColors.length)],
                width: `${8 + Math.random() * 8}px`,
                height: `${8 + Math.random() * 8}px`,
                borderRadius: Math.random() > 0.5 ? '50%' : '2px',
                boxShadow: `0 0 6px ${confettiColors[Math.floor(Math.random() * confettiColors.length)]}`,
              }}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      <div
        className="relative max-w-sm w-full animate-bounce-in"
        style={{
          background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.95) 0%, rgba(49, 46, 129, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(0, 229, 204, 0.3)',
          borderRadius: '32px',
          boxShadow: '0 0 60px rgba(0, 229, 204, 0.3), 0 0 100px rgba(168, 85, 247, 0.2)',
          padding: '32px',
        }}
      >
        {/* Animated glow ring */}
        <div
          className="absolute -top-8 left-1/2 -translate-x-1/2 animate-pulse-glow"
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 30px rgba(0, 229, 204, 0.5), 0 0 60px rgba(168, 85, 247, 0.3)',
          }}
        >
          <span className="text-4xl">⭐</span>
        </div>

        {/* Content */}
        <div className="text-center pt-10">
          <WallyAvatar className="w-20 h-20 mx-auto mb-4 animate-float" />

          <h2 className="text-2xl font-bold text-white mb-2 text-glow-cyan">{message}</h2>

          {/* Rewards */}
          <div className="flex items-center justify-center gap-4 my-6">
            <div className="text-center">
              <div
                className="px-6 py-3 rounded-2xl mb-2"
                style={{
                  background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(124, 58, 237, 0.2) 100%)',
                  border: '1px solid rgba(168, 85, 247, 0.4)',
                  boxShadow: '0 0 20px rgba(168, 85, 247, 0.3)',
                }}
              >
                <span className="text-2xl font-bold text-neo-accent text-glow-purple">+{xpEarned}</span>
              </div>
              <span className="text-sm text-white/50">XP Earned</span>
            </div>

            {coinsEarned > 0 && (
              <div className="text-center">
                <div
                  className="px-6 py-3 rounded-2xl mb-2"
                  style={{
                    background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.3) 0%, rgba(251, 146, 60, 0.2) 100%)',
                    border: '1px solid rgba(250, 204, 21, 0.4)',
                    boxShadow: '0 0 20px rgba(250, 204, 21, 0.3)',
                  }}
                >
                  <span className="text-2xl font-bold text-neo-neon-yellow">+{coinsEarned}</span>
                </div>
                <span className="text-sm text-white/50">Coins</span>
              </div>
            )}
          </div>

          {/* Continue button */}
          <button
            onClick={onClose}
            className="w-full btn-wally py-4 text-lg"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}

export default CelebrationModal;
