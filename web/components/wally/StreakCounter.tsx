'use client';

interface StreakCounterProps {
  streak: number;
  className?: string;
}

export function StreakCounter({ streak, className = '' }: StreakCounterProps) {
  const isOnFire = streak >= 7;

  return (
    <div
      className={`stat-neo ${className}`}
      style={{
        background: isOnFire
          ? 'linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(255, 107, 107, 0.15) 100%)'
          : 'rgba(251, 146, 60, 0.1)',
        borderColor: isOnFire ? 'rgba(251, 146, 60, 0.4)' : 'rgba(251, 146, 60, 0.2)',
      }}
    >
      <span className={`text-xl ${isOnFire ? 'animate-pulse' : ''}`}>
        🔥
      </span>
      <span className={`font-bold text-neo-neon-orange ${isOnFire ? 'text-glow-orange' : ''}`}>
        {streak}
      </span>
    </div>
  );
}

export default StreakCounter;
