'use client';

import { getLevelInfo, getXpProgress } from '@/lib/mockData';

interface XPBarProps {
  xp: number;
  showLevel?: boolean;
  compact?: boolean;
  className?: string;
}

export function XPBar({ xp, showLevel = true, compact = false, className = '' }: XPBarProps) {
  const levelInfo = getLevelInfo(xp);
  const progress = getXpProgress(xp);

  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div
          className="stat-neo"
          style={{
            background: 'rgba(168, 85, 247, 0.15)',
            borderColor: 'rgba(168, 85, 247, 0.3)',
          }}
        >
          <span className="text-sm">⚡</span>
          <span className="text-sm font-bold text-neo-accent text-glow-purple">{xp}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {showLevel && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚡</span>
            <span className="font-bold text-neo-accent text-glow-purple">Level {levelInfo.level}</span>
          </div>
          <span className="text-xs text-white/50">{levelInfo.title}</span>
        </div>
      )}
      <div className="progress-neo">
        <div
          className="progress-neo-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex justify-between mt-2">
        <span className="text-xs text-white/50">{xp} XP</span>
        <span className="text-xs text-white/50">{levelInfo.maxXp} XP</span>
      </div>
    </div>
  );
}

export default XPBar;
