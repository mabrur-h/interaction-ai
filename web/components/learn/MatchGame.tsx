'use client';

import { useState, useEffect } from 'react';
import type { MatchData } from '@/types/game';

interface MatchGameProps {
  data: MatchData;
  onComplete: (correct: boolean) => void;
  className?: string;
}

interface MatchItem {
  id: string;
  pairId: string;
  side: 'left' | 'right';
  label: string;
  emoji?: string;
}

export function MatchGame({ data, onComplete, className = '' }: MatchGameProps) {
  const [leftItems, setLeftItems] = useState<MatchItem[]>([]);
  const [rightItems, setRightItems] = useState<MatchItem[]>([]);
  const [selectedLeft, setSelectedLeft] = useState<MatchItem | null>(null);
  const [selectedRight, setSelectedRight] = useState<MatchItem | null>(null);
  const [matches, setMatches] = useState<Record<string, string>>({}); // leftId -> rightId
  const [showResult, setShowResult] = useState(false);
  const [results, setResults] = useState<Record<string, boolean>>({});

  // Initialize shuffled items
  useEffect(() => {
    const left: MatchItem[] = data.pairs.map((p) => ({
      id: `left-${p.id}`,
      pairId: p.id,
      side: 'left',
      label: p.left.label,
      emoji: p.left.emoji,
    }));

    const right: MatchItem[] = data.pairs.map((p) => ({
      id: `right-${p.id}`,
      pairId: p.id,
      side: 'right',
      label: p.right.label,
      emoji: p.right.emoji,
    }));

    // Shuffle both arrays
    setLeftItems(left.sort(() => Math.random() - 0.5));
    setRightItems(right.sort(() => Math.random() - 0.5));
  }, [data.pairs]);

  const handleLeftClick = (item: MatchItem) => {
    if (showResult || matches[item.id]) return;
    setSelectedLeft(item);

    // If right is already selected, try to match
    if (selectedRight) {
      tryMatch(item, selectedRight);
    }
  };

  const handleRightClick = (item: MatchItem) => {
    if (showResult) return;
    // Check if this item is already matched
    const isMatched = Object.values(matches).includes(item.id);
    if (isMatched) return;

    setSelectedRight(item);

    // If left is already selected, try to match
    if (selectedLeft) {
      tryMatch(selectedLeft, item);
    }
  };

  const tryMatch = (left: MatchItem, right: MatchItem) => {
    setMatches((prev) => ({
      ...prev,
      [left.id]: right.id,
    }));
    setSelectedLeft(null);
    setSelectedRight(null);
  };

  const handleCheck = () => {
    const itemResults: Record<string, boolean> = {};
    let allCorrect = true;

    Object.entries(matches).forEach(([leftId, rightId]) => {
      const leftItem = leftItems.find((i) => i.id === leftId);
      const rightItem = rightItems.find((i) => i.id === rightId);

      if (leftItem && rightItem) {
        const isCorrect = leftItem.pairId === rightItem.pairId;
        itemResults[leftId] = isCorrect;
        if (!isCorrect) allCorrect = false;
      }
    });

    setResults(itemResults);
    setShowResult(true);

    setTimeout(() => {
      onComplete(allCorrect);
    }, 2000);
  };

  const allMatched = Object.keys(matches).length === data.pairs.length;

  const getLeftStyle = (item: MatchItem): React.CSSProperties => {
    if (matches[item.id]) {
      if (showResult) {
        return {
          background: results[item.id]
            ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
            : 'linear-gradient(135deg, rgba(255, 107, 107, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
          border: `2px solid ${results[item.id] ? 'rgba(74, 222, 128, 0.5)' : 'rgba(255, 107, 107, 0.5)'}`,
          boxShadow: results[item.id] ? '0 0 15px rgba(74, 222, 128, 0.3)' : '0 0 15px rgba(255, 107, 107, 0.3)',
        };
      }
      return {
        background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)',
        border: '2px solid rgba(0, 229, 204, 0.4)',
      };
    }
    if (selectedLeft?.id === item.id) {
      return {
        background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.3) 0%, rgba(168, 85, 247, 0.2) 100%)',
        border: '2px solid rgba(0, 229, 204, 0.5)',
        transform: 'scale(1.05)',
        boxShadow: '0 0 20px rgba(0, 229, 204, 0.3)',
      };
    }
    return {
      background: 'rgba(255, 255, 255, 0.03)',
      border: '2px solid rgba(255, 255, 255, 0.1)',
    };
  };

  const getRightStyle = (item: MatchItem): React.CSSProperties => {
    const isMatched = Object.values(matches).includes(item.id);
    if (isMatched) {
      const leftId = Object.entries(matches).find(([, rId]) => rId === item.id)?.[0];
      if (showResult && leftId) {
        return {
          background: results[leftId]
            ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
            : 'linear-gradient(135deg, rgba(255, 107, 107, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
          border: `2px solid ${results[leftId] ? 'rgba(74, 222, 128, 0.5)' : 'rgba(255, 107, 107, 0.5)'}`,
          boxShadow: results[leftId] ? '0 0 15px rgba(74, 222, 128, 0.3)' : '0 0 15px rgba(255, 107, 107, 0.3)',
        };
      }
      return {
        background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)',
        border: '2px solid rgba(0, 229, 204, 0.4)',
      };
    }
    if (selectedRight?.id === item.id) {
      return {
        background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.3) 0%, rgba(168, 85, 247, 0.2) 100%)',
        border: '2px solid rgba(0, 229, 204, 0.5)',
        transform: 'scale(1.05)',
        boxShadow: '0 0 20px rgba(0, 229, 204, 0.3)',
      };
    }
    return {
      background: 'rgba(255, 255, 255, 0.03)',
      border: '2px solid rgba(255, 255, 255, 0.1)',
    };
  };

  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Instruction */}
      <div className="text-center mb-6">
        <p className="text-lg font-medium text-white">{data.instruction}</p>
        <p className="text-sm text-white/50 mt-1">
          Tap one from each side to match
        </p>
      </div>

      {/* Match columns */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Left column */}
        <div className="space-y-3">
          {leftItems.map((item) => {
            const isShaking = showResult && results[item.id] === false;
            return (
              <button
                key={item.id}
                onClick={() => handleLeftClick(item)}
                disabled={showResult || !!matches[item.id]}
                className={`w-full p-3 rounded-2xl transition-all text-center ${isShaking ? 'animate-shake' : ''}`}
                style={getLeftStyle(item)}
              >
                {item.emoji && <span className="text-2xl block mb-1">{item.emoji}</span>}
                <span className="font-medium text-sm text-white">{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Right column */}
        <div className="space-y-3">
          {rightItems.map((item) => {
            const leftId = Object.entries(matches).find(([, rId]) => rId === item.id)?.[0];
            const isShaking = showResult && leftId && results[leftId] === false;
            return (
              <button
                key={item.id}
                onClick={() => handleRightClick(item)}
                disabled={showResult || Object.values(matches).includes(item.id)}
                className={`w-full p-3 rounded-2xl transition-all text-center ${isShaking ? 'animate-shake' : ''}`}
                style={getRightStyle(item)}
              >
                {item.emoji && <span className="text-2xl block mb-1">{item.emoji}</span>}
                <span className="font-medium text-sm text-white">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Check button */}
      {allMatched && !showResult && (
        <button
          onClick={handleCheck}
          className="w-full btn-wally py-3"
        >
          Check Matches
        </button>
      )}

      {/* Result message */}
      {showResult && (
        <div
          className="p-4 rounded-2xl text-center"
          style={{
            background: Object.values(results).every(Boolean)
              ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(255, 107, 107, 0.1) 100%)',
            border: `1px solid ${
              Object.values(results).every(Boolean)
                ? 'rgba(74, 222, 128, 0.4)'
                : 'rgba(251, 146, 60, 0.4)'
            }`,
          }}
        >
          <span className="text-3xl">
            {Object.values(results).every(Boolean) ? '🎉' : '💪'}
          </span>
          <p className="font-medium mt-2 text-white">
            {Object.values(results).every(Boolean)
              ? 'Perfect matches!'
              : 'Good try! Keep practicing!'}
          </p>
        </div>
      )}
    </div>
  );
}

export default MatchGame;
