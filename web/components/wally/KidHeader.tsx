'use client';

import { StreakCounter } from './StreakCounter';
import { XPBar } from './XPBar';
import { CoinBalance } from './CoinBalance';
import { mockUserStats } from '@/lib/mockData';

interface KidHeaderProps {
  title?: string;
  showStats?: boolean;
  className?: string;
}

export function KidHeader({ title, showStats = true, className = '' }: KidHeaderProps) {
  const stats = mockUserStats; // Will be replaced with real data later

  return (
    <header
      className={`sticky top-0 z-40 ${className}`}
      style={{
        background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.8) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
    >
      <div className="px-4 py-3 relative">
        {/* Subtle glow effect at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neo-primary/30 to-transparent" />

        {/* Top row - Stats */}
        {showStats && (
          <div className="flex items-center justify-between mb-2">
            <StreakCounter streak={stats.streak} />
            <div className="flex items-center gap-2">
              <XPBar xp={stats.xp} compact />
              <CoinBalance coins={stats.coins} />
            </div>
          </div>
        )}

        {/* Title row */}
        {title && (
          <h1 className="text-xl font-bold text-white">{title}</h1>
        )}
      </div>
    </header>
  );
}

export default KidHeader;
