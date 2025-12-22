'use client';

import type { Badge, UserBadge } from '@/types/game';

interface BadgeCardProps {
  badge: Badge;
  userBadge?: UserBadge;
  className?: string;
}

export function BadgeCard({ badge, userBadge, className = '' }: BadgeCardProps) {
  const isEarned = !!userBadge;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const categoryGradients: Record<string, { bg: string; border: string; glow: string }> = {
    saving: {
      bg: 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)',
      border: 'rgba(74, 222, 128, 0.4)',
      glow: 'rgba(74, 222, 128, 0.3)',
    },
    learning: {
      bg: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%)',
      border: 'rgba(168, 85, 247, 0.4)',
      glow: 'rgba(168, 85, 247, 0.3)',
    },
    tasks: {
      bg: 'linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(255, 107, 107, 0.1) 100%)',
      border: 'rgba(251, 146, 60, 0.4)',
      glow: 'rgba(251, 146, 60, 0.3)',
    },
    streak: {
      bg: 'linear-gradient(135deg, rgba(255, 107, 107, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
      border: 'rgba(255, 107, 107, 0.4)',
      glow: 'rgba(255, 107, 107, 0.3)',
    },
    social: {
      bg: 'linear-gradient(135deg, rgba(244, 114, 182, 0.2) 0%, rgba(251, 113, 133, 0.1) 100%)',
      border: 'rgba(244, 114, 182, 0.4)',
      glow: 'rgba(244, 114, 182, 0.3)',
    },
  };

  const categoryStyle = categoryGradients[badge.category] || categoryGradients.learning;

  return (
    <div
      className={`relative rounded-3xl p-4 transition-all duration-300 ${
        isEarned
          ? 'hover:scale-[1.03] cursor-pointer'
          : 'opacity-50'
      } ${className}`}
      style={{
        background: isEarned
          ? categoryStyle.bg
          : 'rgba(255, 255, 255, 0.03)',
        border: `1px solid ${isEarned ? categoryStyle.border : 'rgba(255, 255, 255, 0.1)'}`,
        boxShadow: isEarned ? `0 0 25px ${categoryStyle.glow}` : 'none',
      }}
    >
      {/* Badge icon */}
      <div className="text-center mb-3">
        <div
          className={`inline-flex w-16 h-16 rounded-full items-center justify-center text-3xl ${
            isEarned ? 'animate-float' : ''
          }`}
          style={{
            background: isEarned
              ? `linear-gradient(135deg, ${categoryStyle.border} 0%, ${categoryStyle.glow} 100%)`
              : 'rgba(255, 255, 255, 0.05)',
            border: `2px solid ${isEarned ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
            boxShadow: isEarned ? `0 0 20px ${categoryStyle.glow}` : 'none',
          }}
        >
          {isEarned ? badge.emoji : '🔒'}
        </div>
      </div>

      {/* Badge info */}
      <div className="text-center">
        <h3 className={`font-bold ${isEarned ? 'text-white text-glow-cyan' : 'text-white/40'}`}>
          {badge.name}
        </h3>
        <p className={`text-xs mt-1 ${isEarned ? 'text-white/60' : 'text-white/30'}`}>
          {badge.description}
        </p>

        {/* Reward or requirement */}
        {isEarned ? (
          <div className="mt-2">
            <span className="text-xs text-white/40">
              Earned {formatDate(userBadge.earnedAt)}
            </span>
          </div>
        ) : (
          <div className="mt-2 text-xs text-white/30">{badge.requirement}</div>
        )}
      </div>

      {/* XP badge */}
      {isEarned && (
        <div
          className="absolute -top-2 -right-2 text-white text-xs font-bold px-3 py-1 rounded-full"
          style={{
            background: 'linear-gradient(135deg, #A855F7 0%, #7C3AED 100%)',
            boxShadow: '0 0 15px rgba(168, 85, 247, 0.5)',
          }}
        >
          +{badge.xpReward} XP
        </div>
      )}
    </div>
  );
}

export default BadgeCard;
