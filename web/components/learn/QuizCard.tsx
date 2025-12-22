'use client';

import { useState } from 'react';
import { WallyAvatar } from '@/components/wally';
import type { QuizData } from '@/types/game';

interface QuizCardProps {
  data: QuizData;
  onAnswer: (correct: boolean) => void;
  className?: string;
}

export function QuizCard({ data, onAnswer, className = '' }: QuizCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);

  const handleSelect = (optionId: string) => {
    if (showResult) return;

    setSelected(optionId);
    setShowResult(true);

    const isCorrect = optionId === data.correctId;

    // Delay before calling onAnswer to show feedback
    setTimeout(() => {
      onAnswer(isCorrect);
    }, 1500);
  };

  const getOptionStyle = (optionId: string): React.CSSProperties => {
    const base: React.CSSProperties = {
      background: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      transition: 'all 0.3s ease',
    };

    if (!showResult) {
      return base;
    }

    if (optionId === data.correctId) {
      return {
        ...base,
        background: 'rgba(74, 222, 128, 0.15)',
        borderColor: 'rgba(74, 222, 128, 0.5)',
        boxShadow: '0 0 20px rgba(74, 222, 128, 0.3)',
      };
    }

    if (optionId === selected && optionId !== data.correctId) {
      return {
        ...base,
        background: 'rgba(255, 107, 107, 0.15)',
        borderColor: 'rgba(255, 107, 107, 0.5)',
        boxShadow: '0 0 20px rgba(255, 107, 107, 0.3)',
      };
    }

    return {
      ...base,
      opacity: 0.4,
    };
  };

  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Question header */}
      <div className="text-center mb-6">
        <WallyAvatar className="w-16 h-16 mx-auto mb-3 animate-float" />
        <p className="text-lg font-medium text-white">{data.question}</p>
      </div>

      {/* Options grid */}
      <div className="grid grid-cols-2 gap-3">
        {data.options.map((option) => (
          <button
            key={option.id}
            onClick={() => handleSelect(option.id)}
            disabled={showResult}
            style={getOptionStyle(option.id)}
            className={`p-4 rounded-2xl transition-all hover:scale-[1.02] active:scale-[0.98] ${
              showResult && option.id === selected && option.id !== data.correctId
                ? 'animate-shake'
                : ''
            }`}
          >
            {option.emoji && (
              <span className="text-3xl block mb-1">{option.emoji}</span>
            )}
            <span className="text-sm font-medium text-white/80">{option.label}</span>
          </button>
        ))}
      </div>

      {/* Explanation */}
      {showResult && data.explanation && (
        <div
          className="mt-4 p-4 rounded-2xl"
          style={{
            background:
              selected === data.correctId
                ? 'rgba(74, 222, 128, 0.1)'
                : 'rgba(251, 146, 60, 0.1)',
            border: `1px solid ${
              selected === data.correctId
                ? 'rgba(74, 222, 128, 0.3)'
                : 'rgba(251, 146, 60, 0.3)'
            }`,
          }}
        >
          <div className="flex items-start gap-3">
            <span className="text-2xl">
              {selected === data.correctId ? '🎉' : '💡'}
            </span>
            <p className="text-sm text-white/80">{data.explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuizCard;
