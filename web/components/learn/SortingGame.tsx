'use client';

import { useState } from 'react';
import type { SortingData, SortingItem } from '@/types/game';

interface SortingGameProps {
  data: SortingData;
  onComplete: (correct: boolean) => void;
  className?: string;
}

export function SortingGame({ data, onComplete, className = '' }: SortingGameProps) {
  const [sortedItems, setSortedItems] = useState<Record<string, string[]>>(() => {
    const initial: Record<string, string[]> = {};
    data.categories.forEach((cat) => {
      initial[cat.id] = [];
    });
    return initial;
  });
  const [unsortedItems, setUnsortedItems] = useState<SortingItem[]>(data.items);
  const [selectedItem, setSelectedItem] = useState<SortingItem | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [results, setResults] = useState<Record<string, boolean>>({});

  const handleItemClick = (item: SortingItem) => {
    if (showResult) return;
    setSelectedItem(item);
  };

  const handleCategoryClick = (categoryId: string) => {
    if (!selectedItem || showResult) return;

    // Move item to category
    setSortedItems((prev) => ({
      ...prev,
      [categoryId]: [...prev[categoryId], selectedItem.id],
    }));
    setUnsortedItems((prev) => prev.filter((i) => i.id !== selectedItem.id));
    setSelectedItem(null);
  };

  const handleCheck = () => {
    // Check all placements
    const itemResults: Record<string, boolean> = {};
    let allCorrect = true;

    Object.entries(sortedItems).forEach(([categoryId, itemIds]) => {
      itemIds.forEach((itemId) => {
        const item = data.items.find((i) => i.id === itemId);
        const isCorrect = item?.correctCategoryId === categoryId;
        itemResults[itemId] = isCorrect;
        if (!isCorrect) allCorrect = false;
      });
    });

    setResults(itemResults);
    setShowResult(true);

    setTimeout(() => {
      onComplete(allCorrect);
    }, 2000);
  };

  const allSorted = unsortedItems.length === 0;

  const getItemById = (id: string) => data.items.find((i) => i.id === id);

  return (
    <div className={`card-wally p-6 ${className}`}>
      {/* Instruction */}
      <div className="text-center mb-6">
        <p className="text-lg font-medium text-white">{data.instruction}</p>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {data.categories.map((category) => (
          <button
            key={category.id}
            onClick={() => handleCategoryClick(category.id)}
            disabled={!selectedItem || showResult}
            className="p-4 rounded-2xl min-h-[120px] transition-all"
            style={{
              background: selectedItem
                ? 'linear-gradient(135deg, rgba(0, 229, 204, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%)'
                : 'rgba(255, 255, 255, 0.03)',
              border: selectedItem
                ? '2px dashed rgba(0, 229, 204, 0.5)'
                : '2px dashed rgba(255, 255, 255, 0.1)',
              cursor: selectedItem && !showResult ? 'pointer' : 'default',
            }}
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              {category.emoji && <span className="text-xl">{category.emoji}</span>}
              <span className="font-bold text-white">{category.label}</span>
            </div>

            {/* Sorted items in this category */}
            <div className="flex flex-wrap gap-2 justify-center mt-2">
              {sortedItems[category.id].map((itemId) => {
                const item = getItemById(itemId);
                if (!item) return null;

                const result = results[itemId];
                const showItemResult = showResult && result !== undefined;

                return (
                  <div
                    key={itemId}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                      showItemResult && !result ? 'animate-shake' : ''
                    }`}
                    style={{
                      background: showItemResult
                        ? result
                          ? 'rgba(74, 222, 128, 0.2)'
                          : 'rgba(255, 107, 107, 0.2)'
                        : 'rgba(255, 255, 255, 0.1)',
                      border: `1px solid ${
                        showItemResult
                          ? result
                            ? 'rgba(74, 222, 128, 0.5)'
                            : 'rgba(255, 107, 107, 0.5)'
                          : 'rgba(255, 255, 255, 0.2)'
                      }`,
                      color: showItemResult
                        ? result
                          ? '#4ADE80'
                          : '#FF6B6B'
                        : 'white',
                    }}
                  >
                    {item.emoji} {item.label}
                  </div>
                );
              })}
            </div>
          </button>
        ))}
      </div>

      {/* Unsorted items */}
      {unsortedItems.length > 0 && (
        <div className="mb-6">
          <p className="text-sm text-white/50 mb-3 text-center">
            Tap an item, then tap a category
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {unsortedItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleItemClick(item)}
                className="px-4 py-2 rounded-full transition-all"
                style={{
                  background: selectedItem?.id === item.id
                    ? 'linear-gradient(135deg, rgba(0, 229, 204, 0.3) 0%, rgba(168, 85, 247, 0.2) 100%)'
                    : 'rgba(255, 255, 255, 0.05)',
                  border: selectedItem?.id === item.id
                    ? '2px solid rgba(0, 229, 204, 0.5)'
                    : '2px solid rgba(255, 255, 255, 0.1)',
                  transform: selectedItem?.id === item.id ? 'scale(1.05)' : 'scale(1)',
                  boxShadow: selectedItem?.id === item.id ? '0 0 20px rgba(0, 229, 204, 0.3)' : 'none',
                }}
              >
                <span className="text-xl mr-1">{item.emoji}</span>
                <span className="font-medium text-white">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Check button */}
      {allSorted && !showResult && (
        <button
          onClick={handleCheck}
          className="w-full btn-wally py-3"
        >
          Check My Answers
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
              ? 'Perfect! You got them all right!'
              : 'Good try! Keep learning!'}
          </p>
        </div>
      )}
    </div>
  );
}

export default SortingGame;
