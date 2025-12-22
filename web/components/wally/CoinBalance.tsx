'use client';

interface CoinBalanceProps {
  coins: number;
  className?: string;
}

export function CoinBalance({ coins, className = '' }: CoinBalanceProps) {
  return (
    <div
      className={`stat-neo ${className}`}
      style={{
        background: 'rgba(250, 204, 21, 0.15)',
        borderColor: 'rgba(250, 204, 21, 0.3)',
      }}
    >
      <span className="text-xl">🪙</span>
      <span className="font-bold text-neo-neon-yellow">
        {coins.toLocaleString()}
      </span>
    </div>
  );
}

export default CoinBalance;
