'use client';

import type { Lesson } from '@/types/game';
import { LessonCard } from './LessonCard';

interface LessonMapProps {
  lessons: Lesson[];
  className?: string;
}

export function LessonMap({ lessons, className = '' }: LessonMapProps) {
  const sortedLessons = [...lessons].sort((a, b) => a.order - b.order);

  return (
    <div className={`relative ${className}`}>
      {/* Path connector line with neo gradient */}
      <div
        className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 rounded-full"
        style={{
          background: 'linear-gradient(180deg, #00E5CC 0%, #A855F7 50%, rgba(255, 255, 255, 0.1) 100%)',
          boxShadow: '0 0 15px rgba(0, 229, 204, 0.3)',
        }}
      />

      {/* Lessons */}
      <div className="relative space-y-6">
        {sortedLessons.map((lesson, index) => (
          <div
            key={lesson.id}
            className={`relative ${
              index % 2 === 0 ? 'pr-4 md:pr-0 md:mr-auto md:w-[48%]' : 'pl-4 md:pl-0 md:ml-auto md:w-[48%]'
            }`}
          >
            {/* Connection dot */}
            <div
              className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full ${
                index % 2 === 0 ? 'right-0 md:right-auto md:left-full md:ml-[calc(4%-8px)]' : 'left-0 md:left-auto md:right-full md:mr-[calc(4%-8px)]'
              } hidden md:block`}
              style={{
                background: lesson.progress === 100
                  ? 'linear-gradient(135deg, #4ADE80 0%, #00E5CC 100%)'
                  : lesson.locked
                  ? 'rgba(255, 255, 255, 0.1)'
                  : 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
                boxShadow: lesson.progress === 100
                  ? '0 0 10px rgba(74, 222, 128, 0.5)'
                  : lesson.locked
                  ? 'none'
                  : '0 0 10px rgba(0, 229, 204, 0.5)',
                border: '3px solid rgba(15, 23, 42, 0.8)',
              }}
            />

            {/* Lesson number bubble - mobile */}
            <div
              className="absolute -left-3 top-6 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold md:hidden"
              style={{
                background: lesson.progress === 100
                  ? 'linear-gradient(135deg, #4ADE80 0%, #00E5CC 100%)'
                  : lesson.locked
                  ? 'rgba(255, 255, 255, 0.1)'
                  : 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
                boxShadow: lesson.progress === 100
                  ? '0 0 15px rgba(74, 222, 128, 0.4)'
                  : lesson.locked
                  ? 'none'
                  : '0 0 15px rgba(0, 229, 204, 0.4)',
                color: lesson.locked ? 'rgba(255, 255, 255, 0.4)' : 'white',
              }}
            >
              {lesson.progress === 100 ? '✓' : index + 1}
            </div>

            <LessonCard lesson={lesson} />
          </div>
        ))}
      </div>

      {/* Start marker */}
      <div className="absolute -top-4 left-1/2 -translate-x-1/2">
        <div
          className="rounded-full p-2"
          style={{
            background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.9) 0%, rgba(49, 46, 129, 0.8) 100%)',
            border: '2px solid rgba(0, 229, 204, 0.4)',
            boxShadow: '0 0 20px rgba(0, 229, 204, 0.3)',
          }}
        >
          <span className="text-2xl">🏠</span>
        </div>
      </div>

      {/* End marker */}
      <div className="absolute -bottom-4 left-1/2 -translate-x-1/2">
        <div
          className="rounded-full p-2"
          style={{
            background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
            border: '2px solid rgba(250, 204, 21, 0.4)',
            boxShadow: '0 0 20px rgba(250, 204, 21, 0.3)',
          }}
        >
          <span className="text-2xl">🏆</span>
        </div>
      </div>
    </div>
  );
}

export default LessonMap;
