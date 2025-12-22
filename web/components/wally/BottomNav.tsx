'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { NavItem } from '@/types/game';

const navItems: NavItem[] = [
  { href: '/', icon: '💬', label: 'Chat' },
  { href: '/learn', icon: '📚', label: 'Learn' },
  { href: '/tasks', icon: '✅', label: 'Tasks' },
  { href: '/piggy-bank', icon: '🐷', label: 'Save' },
  { href: '/profile', icon: '⭐', label: 'Me' },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-4 left-4 right-4 z-50 safe-area-bottom">
      <div className="nav-neo mx-auto max-w-md px-2 py-2">
        <div className="flex justify-around items-center">
          {navItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex flex-col items-center gap-1 px-4 py-2 rounded-2xl transition-all duration-300 ${
                  isActive
                    ? 'bg-gradient-to-r from-neo-primary/20 to-neo-accent/20'
                    : 'hover:bg-white/5'
                }`}
              >
                {/* Glow effect for active item */}
                {isActive && (
                  <div className="absolute inset-0 rounded-2xl bg-neo-primary/10 blur-lg" />
                )}

                <span
                  className={`relative text-2xl transition-all duration-300 ${
                    isActive ? 'scale-110 animate-float' : ''
                  }`}
                >
                  {item.icon}
                </span>

                <span
                  className={`relative text-xs font-medium transition-all ${
                    isActive
                      ? 'text-neo-primary text-glow-cyan'
                      : 'text-white/50'
                  }`}
                >
                  {item.label}
                </span>

                {/* Active indicator dot */}
                {isActive && (
                  <div className="absolute -bottom-0.5 w-1.5 h-1.5 rounded-full bg-neo-primary shadow-neo-sm" />
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

export default BottomNav;
