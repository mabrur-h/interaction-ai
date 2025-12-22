'use client';

import { useState } from 'react';
import type { BudgetData } from '@/types/game';

interface BudgetSliderProps {
  data: BudgetData;
  onComplete: (allocation: Record<string, number>) => void;
  className?: string;
}

export function BudgetSlider({ data, onComplete, className = '' }: BudgetSliderProps) {
  const [allocations, setAllocations] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    const equalSplit = Math.floor(100 / data.categories.length);
    data.categories.forEach((cat, index) => {
      if (index === data.categories.length - 1) {
        // Give remainder to last category
        initial[cat.id] = 100 - equalSplit * (data.categories.length - 1);
      } else {
        initial[cat.id] = equalSplit;
      }
    });
    return initial;
  });
  const [showResult, setShowResult] = useState(false);

  const handleSliderChange = (categoryId: string, newValue: number) => {
    const oldValue = allocations[categoryId];
    const diff = newValue - oldValue;

    // Find other categories to adjust
    const otherCategories = data.categories.filter((c) => c.id !== categoryId);
    const otherTotal = otherCategories.reduce(
      (sum, c) => sum + allocations[c.id],
      0
    );

    if (otherTotal === 0 && diff > 0) return;

    // Distribute the difference among other categories proportionally
    const newAllocations = { ...allocations, [categoryId]: newValue };

    if (diff !== 0 && otherTotal > 0) {
      const remainingDiff = -diff;
      otherCategories.forEach((cat) => {
        const proportion = allocations[cat.id] / otherTotal;
        let adjustment = Math.round(remainingDiff * proportion);

        // Ensure minimum values are respected
        const minVal = cat.minPercent || 0;
        const newCatValue = allocations[cat.id] + adjustment;

        if (newCatValue < minVal) {
          adjustment = minVal - allocations[cat.id];
        }
        if (newCatValue > 100) {
          adjustment = 100 - allocations[cat.id];
        }

        newAllocations[cat.id] = Math.max(0, Math.min(100, allocations[cat.id] + adjustment));
      });
    }

    // Normalize to ensure sum is exactly 100
    const newTotal = Object.values(newAllocations).reduce((sum, v) => sum + v, 0);
    if (newTotal !== 100) {
      const lastCat = otherCategories[otherCategories.length - 1];
      if (lastCat) {
        newAllocations[lastCat.id] += 100 - newTotal;
      }
    }

    setAllocations(newAllocations);
  };

  const handleConfirm = () => {
    setShowResult(true);
    setTimeout(() => {
      onComplete(allocations);
    }, 1500);
  };

  const formatAmount = (percent: number) => {
    const amount = Math.round((percent / 100) * data.totalAmount);
    return amount.toLocaleString();
  };

  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Instruction */}
      <div className="text-center mb-6">
        <p className="text-lg font-medium text-white">{data.instruction}</p>
        <p
          className="text-2xl font-bold mt-2 text-glow-cyan"
          style={{ color: '#00E5CC' }}
        >
          {data.totalAmount.toLocaleString()} so&apos;m
        </p>
      </div>

      {/* Sliders */}
      <div className="space-y-6 mb-6">
        {data.categories.map((category) => {
          const percent = allocations[category.id];
          const amount = formatAmount(percent);

          return (
            <div key={category.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{category.emoji}</span>
                  <span className="font-medium text-white">{category.label}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-lg text-neo-accent">{percent}%</span>
                  <span className="text-sm text-white/50 block">{amount} so&apos;m</span>
                </div>
              </div>

              <div className="relative h-3">
                <input
                  type="range"
                  min={category.minPercent || 0}
                  max={category.maxPercent || 100}
                  value={percent}
                  onChange={(e) => handleSliderChange(category.id, parseInt(e.target.value))}
                  disabled={showResult}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                {/* Track background */}
                <div
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                />
                {/* Progress bar */}
                <div
                  className="absolute top-0 left-0 h-full rounded-full transition-all"
                  style={{
                    width: `${percent}%`,
                    background: 'linear-gradient(90deg, #00E5CC 0%, #A855F7 100%)',
                    boxShadow: '0 0 10px rgba(0, 229, 204, 0.5)',
                  }}
                />
                {/* Thumb indicator */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-5 h-5 rounded-full transition-all"
                  style={{
                    left: `calc(${percent}% - 10px)`,
                    background: 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
                    border: '3px solid rgba(15, 23, 42, 0.8)',
                    boxShadow: '0 0 15px rgba(0, 229, 204, 0.5)',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Suggested split hint */}
      {data.suggestedSplit && !showResult && (
        <div
          className="rounded-2xl p-3 mb-4"
          style={{
            background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%)',
            border: '1px solid rgba(168, 85, 247, 0.3)',
          }}
        >
          <p className="text-sm text-center" style={{ color: '#A855F7' }}>
            💡 Tip: Try saving at least {data.suggestedSplit.save || 50}%!
          </p>
        </div>
      )}

      {/* Confirm button */}
      {!showResult && (
        <button
          onClick={handleConfirm}
          className="w-full btn-wally py-3"
        >
          Confirm My Split
        </button>
      )}

      {/* Result */}
      {showResult && (
        <div
          className="rounded-2xl p-4 text-center"
          style={{
            background: 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)',
            border: '1px solid rgba(74, 222, 128, 0.4)',
          }}
        >
          <span className="text-3xl">🎉</span>
          <p className="font-medium mt-2" style={{ color: '#4ADE80' }}>
            Great job thinking about your budget!
          </p>
        </div>
      )}
    </div>
  );
}

export default BudgetSlider;
