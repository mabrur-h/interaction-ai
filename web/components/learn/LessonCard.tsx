'use client';

import Link from 'next/link';
import type { Lesson } from '@/types/game';

interface LessonCardProps {
  lesson: Lesson;
  className?: string;
}

export function LessonCard({ lesson, className = '' }: LessonCardProps) {
  const isCompleted = lesson.progress === 100;
  const isStarted = lesson.progress > 0 && lesson.progress < 100;

  const content = (
    <div
      className={`card-wally p-5 relative transition-all duration-300 ${
        lesson.locked
          ? 'opacity-40'
          : 'hover:scale-[1.02] hover:shadow-neo active:scale-[0.98] cursor-pointer'
      } ${className}`}
    >
      {/* Glow effect for completed */}
      {isCompleted && (
        <div className="absolute inset-0 rounded-3xl bg-neo-neon-green/5 animate-pulse-glow" />
      )}

      {/* Completion badge */}
      {isCompleted && (
        <div
          className="absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center shadow-neo"
          style={{
            background: 'linear-gradient(135deg, #4ADE80 0%, #00E5CC 100%)',
          }}
        >
          <span className="text-white text-lg">✓</span>
        </div>
      )}

      {/* Lesson icon and title */}
      <div className="relative flex items-center gap-4 mb-4">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl relative overflow-hidden"
          style={{
            background: isCompleted
              ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
              : isStarted
              ? 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <span className="animate-float">{lesson.emoji}</span>
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-white text-lg">{lesson.title}</h3>
          <p className="text-sm text-white/50">{lesson.description}</p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-3 mb-3">
        <div className="flex-1 progress-neo">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${lesson.progress}%`,
              background: isCompleted
                ? 'linear-gradient(90deg, #4ADE80 0%, #00E5CC 100%)'
                : 'linear-gradient(90deg, #00E5CC 0%, #A855F7 100%)',
              boxShadow: isCompleted
                ? '0 0 10px rgba(74, 222, 128, 0.5)'
                : '0 0 10px rgba(0, 229, 204, 0.5)',
            }}
          />
        </div>
        <span
          className={`text-sm font-medium ${
            isCompleted ? 'text-neo-neon-green' : 'text-white/60'
          }`}
        >
          {lesson.progress}%
        </span>
      </div>

      {/* XP reward */}
      <div className="flex items-center gap-1.5 badge-neo-purple w-fit">
        <span>⚡</span>
        <span className="font-medium">+{lesson.xpReward} XP</span>
      </div>

      {/* Locked overlay */}
      {lesson.locked && (
        <div
          className="absolute inset-0 rounded-3xl flex items-center justify-center"
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            backdropFilter: 'blur(4px)',
          }}
        >
          <div
            className="rounded-full p-4"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <span className="text-4xl">🔒</span>
          </div>
        </div>
      )}
    </div>
  );

  if (lesson.locked) {
    return content;
  }

  return (
    <Link href={`/learn/${lesson.id}`}>
      {content}
    </Link>
  );
}

export default LessonCard;
