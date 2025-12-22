'use client';

import Link from 'next/link';
import { WallyAvatar } from './WallyOwl';

interface WallyChatHeaderProps {
  childName: string;
  balance?: number;
  onLogout: () => void;
}

// Format amount in UZS (amount is already in so'm)
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('uz-UZ').format(amount);
}

export function WallyChatHeader({ childName, balance, onLogout }: WallyChatHeaderProps) {
  return (
    <header className="mb-4 flex items-center justify-between bg-white rounded-2xl shadow-md p-3">
      <div className="flex items-center gap-3">
        <WallyAvatar className="w-12 h-12" />
        <div>
          <h1 className="text-lg font-bold text-violet-700">Wally Junior</h1>
          <p className="text-sm text-gray-500">Hi, {childName}!</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Balance display */}
        {balance !== undefined && (
          <div className="bg-teal-50 rounded-xl px-4 py-2 text-center">
            <p className="text-xs text-teal-600">Balance</p>
            <p className="text-lg font-bold text-teal-700">{formatMoney(balance)}</p>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex gap-2">
          <Link
            href="/piggy-bank"
            className="flex items-center gap-1 rounded-xl bg-pink-50 px-3 py-2 text-pink-600 hover:bg-pink-100 transition-colors"
          >
            <span className="text-xl">🐷</span>
            <span className="hidden sm:inline text-sm font-medium">Goals</span>
          </Link>
        </nav>

        {/* Logout */}
        <button
          onClick={onLogout}
          className="rounded-xl border-2 border-gray-200 px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 transition-colors"
        >
          Bye!
        </button>
      </div>
    </header>
  );
}

export default WallyChatHeader;
