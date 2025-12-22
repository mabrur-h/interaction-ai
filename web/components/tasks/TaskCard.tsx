'use client';

import { useState } from 'react';
import type { Task } from '@/types/game';

interface TaskCardProps {
  task: Task;
  onComplete?: (taskId: string) => void;
  className?: string;
}

export function TaskCard({ task, onComplete, className = '' }: TaskCardProps) {
  const [isCompleting, setIsCompleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const isCompleted = task.status === 'completed';
  const isExpired = task.status === 'expired';

  const formatDueDate = (dateStr?: string) => {
    if (!dateStr) return null;

    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const handleComplete = async () => {
    if (!onComplete || isCompleted || isExpired) return;

    setIsCompleting(true);
    // Simulate completion delay
    await new Promise((resolve) => setTimeout(resolve, 500));
    onComplete(task.id);
    setShowConfirm(false);
    setIsCompleting(false);
  };

  const dueDate = formatDueDate(task.dueDate);

  return (
    <div
      className={`card-wally p-5 transition-all duration-300 ${
        isCompleted ? 'opacity-60' : ''
      } ${isExpired ? 'opacity-40' : ''} ${className}`}
      style={
        isCompleted
          ? {
              background: 'linear-gradient(135deg, rgba(74, 222, 128, 0.1) 0%, rgba(30, 27, 75, 0.8) 100%)',
            }
          : undefined
      }
    >
      <div className="flex items-start gap-4">
        {/* Task icon */}
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0"
          style={{
            background: isCompleted
              ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
              : task.type === 'learning'
              ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%)'
              : 'linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(255, 107, 107, 0.1) 100%)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          {isCompleted ? '✅' : task.emoji}
        </div>

        {/* Task info */}
        <div className="flex-1 min-w-0">
          <h3
            className={`font-bold text-white ${isCompleted ? 'line-through opacity-60' : ''}`}
          >
            {task.title}
          </h3>

          {task.description && (
            <p className="text-sm text-white/50 mt-0.5 line-clamp-2">
              {task.description}
            </p>
          )}

          <div className="flex items-center gap-3 mt-2 flex-wrap">
            {/* From */}
            <span className="text-sm text-white/40">From: {task.assignedBy}</span>

            {/* Due date */}
            {dueDate && !isCompleted && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  dueDate === 'Today'
                    ? 'badge-neo-orange'
                    : 'text-white/40 bg-white/5 border border-white/10'
                }`}
              >
                Due: {dueDate}
              </span>
            )}
          </div>

          {/* Rewards */}
          <div className="flex items-center gap-3 mt-3">
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm"
              style={{
                background: 'rgba(250, 204, 21, 0.15)',
                border: '1px solid rgba(250, 204, 21, 0.3)',
              }}
            >
              <span>🪙</span>
              <span className="font-bold text-neo-neon-yellow">{task.coinReward}</span>
            </div>
            {task.xpReward && (
              <div className="badge-neo-purple">
                <span>⚡</span>
                <span className="font-medium">+{task.xpReward}</span>
              </div>
            )}
          </div>
        </div>

        {/* Action button */}
        {!isCompleted && !isExpired && (
          <div className="flex-shrink-0">
            {showConfirm ? (
              <div className="flex flex-col gap-2">
                <button
                  onClick={handleComplete}
                  disabled={isCompleting}
                  className="btn-wally px-4 py-2 text-sm"
                >
                  {isCompleting ? '...' : 'Yes!'}
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  className="text-sm text-white/40 hover:text-white/60"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowConfirm(true)}
                className="btn-wally px-4 py-2"
              >
                Done!
              </button>
            )}
          </div>
        )}

        {/* Completed badge */}
        {isCompleted && (
          <div className="flex-shrink-0">
            <span className="text-neo-neon-green font-bold text-sm text-glow-cyan">
              Completed!
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default TaskCard;
