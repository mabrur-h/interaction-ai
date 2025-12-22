'use client';

import { useState } from 'react';
import { WallyAvatar } from '@/components/wally';
import type { StoryData, StoryChoice } from '@/types/game';

interface StoryCardProps {
  data: StoryData;
  onChoice: (choice: StoryChoice) => void;
  className?: string;
}

export function StoryCard({ data, onChoice, className = '' }: StoryCardProps) {
  const [selectedChoice, setSelectedChoice] = useState<StoryChoice | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const handleChoice = (choice: StoryChoice) => {
    if (showFeedback) return;

    setSelectedChoice(choice);
    setShowFeedback(true);

    setTimeout(() => {
      onChoice(choice);
    }, 2500);
  };

  const getChoiceStyle = (choice: StoryChoice): React.CSSProperties => {
    if (!showFeedback) {
      return {
        background: 'rgba(255, 255, 255, 0.03)',
        border: '2px solid rgba(255, 255, 255, 0.1)',
      };
    }

    if (choice.id === selectedChoice?.id) {
      return choice.isGood
        ? {
            background: 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)',
            border: '2px solid rgba(74, 222, 128, 0.5)',
            boxShadow: '0 0 20px rgba(74, 222, 128, 0.3)',
          }
        : {
            background: 'linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(255, 107, 107, 0.1) 100%)',
            border: '2px solid rgba(251, 146, 60, 0.5)',
            boxShadow: '0 0 20px rgba(251, 146, 60, 0.3)',
          };
    }

    return {
      background: 'rgba(255, 255, 255, 0.02)',
      border: '2px solid rgba(255, 255, 255, 0.05)',
      opacity: 0.5,
    };
  };

  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Wally header */}
      <div className="flex items-start gap-4 mb-6">
        <div className="flex-shrink-0">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(0, 229, 204, 0.2) 100%)',
              border: '2px solid rgba(168, 85, 247, 0.3)',
            }}
          >
            <WallyAvatar className="w-12 h-12 animate-float" />
          </div>
        </div>
        <div className="flex-1">
          <div
            className="rounded-2xl rounded-tl-none p-4"
            style={{
              background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%)',
              border: '1px solid rgba(168, 85, 247, 0.3)',
            }}
          >
            <p className="text-sm font-medium mb-1" style={{ color: '#A855F7' }}>
              📖 Story Time!
            </p>
            <p className="text-white/80">{data.story}</p>
          </div>
          {data.wallyMessage && (
            <p className="text-sm text-white/50 mt-2 italic">{data.wallyMessage}</p>
          )}
        </div>
      </div>

      {/* Choices */}
      <div className="space-y-3">
        {data.choices.map((choice) => (
          <button
            key={choice.id}
            onClick={() => handleChoice(choice)}
            disabled={showFeedback}
            className="w-full p-4 rounded-2xl text-left transition-all hover:scale-[1.01]"
            style={getChoiceStyle(choice)}
          >
            <div className="flex items-center gap-3">
              {choice.emoji && <span className="text-2xl">{choice.emoji}</span>}
              <span className="font-medium text-white">{choice.label}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Feedback */}
      {showFeedback && selectedChoice && (
        <div
          className="mt-6 p-4 rounded-2xl"
          style={{
            background: selectedChoice.isGood
              ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.15) 0%, rgba(0, 229, 204, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(255, 107, 107, 0.1) 100%)',
            border: `1px solid ${selectedChoice.isGood ? 'rgba(74, 222, 128, 0.3)' : 'rgba(251, 146, 60, 0.3)'}`,
          }}
        >
          <div className="flex items-start gap-3">
            <span className="text-3xl">
              {selectedChoice.isGood ? '🌟' : '💭'}
            </span>
            <div>
              <p
                className="font-medium mb-1"
                style={{ color: selectedChoice.isGood ? '#4ADE80' : '#FB923C' }}
              >
                {selectedChoice.isGood ? 'Great choice!' : 'Good thinking, but...'}
              </p>
              <p className="text-sm text-white/70">{selectedChoice.feedback}</p>
              {selectedChoice.xpBonus && (
                <p className="text-sm font-medium mt-2 text-glow-purple" style={{ color: '#A855F7' }}>
                  +{selectedChoice.xpBonus} bonus XP!
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StoryCard;
