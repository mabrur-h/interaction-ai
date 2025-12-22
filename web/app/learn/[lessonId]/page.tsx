'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { WallyAvatar } from '@/components/wally';
import {
  QuizCard,
  SortingGame,
  BudgetSlider,
  MatchGame,
  StoryCard,
  InfoCard,
} from '@/components/learn';
import { CelebrationModal } from '@/components/shared';
import { mockLessons } from '@/lib/mockData';
import type {
  Activity,
  QuizData,
  SortingData,
  BudgetData,
  MatchData,
  StoryData,
  InfoData,
} from '@/types/game';

export default function LessonPlayerPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const lessonId = params.lessonId as string;

  const [currentActivityIndex, setCurrentActivityIndex] = useState(0);
  const [xpEarned, setXpEarned] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [lessonComplete, setLessonComplete] = useState(false);

  const isChild = user?.user_type === 'child';
  const lesson = mockLessons.find((l) => l.id === lessonId);

  // Redirect if not authenticated or not a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login/child');
    } else if (!authLoading && isAuthenticated && !isChild) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isChild, router]);

  if (authLoading || !isAuthenticated || !isChild) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent" />
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen wally-bg flex items-center justify-center p-4">
        <div className="card-wally p-8 text-center max-w-md">
          <span className="text-5xl">😕</span>
          <h2 className="text-xl font-bold text-gray-700 mt-4 mb-2">
            Lesson not found
          </h2>
          <Link href="/learn" className="text-teal-600 hover:underline">
            Back to Learn
          </Link>
        </div>
      </div>
    );
  }

  if (lesson.locked) {
    return (
      <div className="min-h-screen wally-bg flex items-center justify-center p-4">
        <div className="card-wally p-8 text-center max-w-md">
          <span className="text-5xl">🔒</span>
          <h2 className="text-xl font-bold text-gray-700 mt-4 mb-2">
            This lesson is locked
          </h2>
          <p className="text-gray-500 mb-4">
            Complete the previous lessons to unlock this one!
          </p>
          <Link href="/learn" className="btn-wally inline-block">
            Back to Learn
          </Link>
        </div>
      </div>
    );
  }

  const activities = lesson.activities;
  const currentActivity = activities[currentActivityIndex];
  const progress = ((currentActivityIndex + 1) / activities.length) * 100;
  const xpPerActivity = Math.floor(lesson.xpReward / activities.length);

  const handleActivityComplete = (correct: boolean, bonusXp: number = 0) => {
    const earnedXp = correct ? xpPerActivity + bonusXp : Math.floor(xpPerActivity / 2);
    setXpEarned((prev) => prev + earnedXp);

    if (currentActivityIndex < activities.length - 1) {
      // Move to next activity
      setTimeout(() => {
        setCurrentActivityIndex((prev) => prev + 1);
      }, 500);
    } else {
      // Lesson complete!
      setLessonComplete(true);
      setShowCelebration(true);
    }
  };

  const handleCelebrationClose = () => {
    setShowCelebration(false);
    router.push('/learn');
  };

  const renderActivity = (activity: Activity) => {
    switch (activity.type) {
      case 'quiz':
        return (
          <QuizCard
            key={activity.id}
            data={activity.data as QuizData}
            onAnswer={(correct) => handleActivityComplete(correct)}
          />
        );

      case 'sorting':
        return (
          <SortingGame
            key={activity.id}
            data={activity.data as SortingData}
            onComplete={(correct) => handleActivityComplete(correct)}
          />
        );

      case 'budget':
        return (
          <BudgetSlider
            key={activity.id}
            data={activity.data as BudgetData}
            onComplete={() => handleActivityComplete(true, 5)}
          />
        );

      case 'match':
        return (
          <MatchGame
            key={activity.id}
            data={activity.data as MatchData}
            onComplete={(correct) => handleActivityComplete(correct)}
          />
        );

      case 'story':
        return (
          <StoryCard
            key={activity.id}
            data={activity.data as StoryData}
            onChoice={(choice) => handleActivityComplete(choice.isGood, choice.xpBonus || 0)}
          />
        );

      case 'info':
        return (
          <InfoCard
            key={activity.id}
            data={activity.data as InfoData}
            onContinue={() => handleActivityComplete(true)}
          />
        );

      default:
        return (
          <div className="card-wally p-6 text-center">
            <p className="text-gray-500">Unknown activity type</p>
            <button
              onClick={() => handleActivityComplete(true)}
              className="btn-wally mt-4"
            >
              Skip
            </button>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen wally-bg">
      {/* Header */}
      <header className="sticky top-0 bg-white/90 backdrop-blur-sm z-40 border-b border-teal-100">
        <div className="px-4 py-3">
          {/* Top row - Close and progress */}
          <div className="flex items-center gap-4 mb-2">
            <Link
              href="/learn"
              className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200"
            >
              ✕
            </Link>

            {/* Progress bar */}
            <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-teal-400 to-teal-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* XP earned */}
            <div className="flex items-center gap-1 bg-purple-100 px-3 py-1 rounded-full">
              <span className="text-sm">⚡</span>
              <span className="text-sm font-bold text-purple-600">{xpEarned}</span>
            </div>
          </div>

          {/* Lesson title */}
          <div className="flex items-center gap-2">
            <span className="text-2xl">{lesson.emoji}</span>
            <h1 className="font-bold text-gray-800">{lesson.title}</h1>
          </div>
        </div>
      </header>

      {/* Activity content */}
      <div className="p-4 max-w-2xl mx-auto">
        {activities.length === 0 ? (
          <div className="card-wally p-8 text-center">
            <WallyAvatar className="w-20 h-20 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-700 mb-2">
              Coming Soon!
            </h2>
            <p className="text-gray-500 mb-4">
              This lesson is still being prepared.
            </p>
            <Link href="/learn" className="btn-wally inline-block">
              Back to Learn
            </Link>
          </div>
        ) : (
          <div className="animate-bounce-in">
            {renderActivity(currentActivity)}
          </div>
        )}

        {/* Activity counter */}
        {activities.length > 0 && (
          <div className="text-center mt-4 text-sm text-gray-500">
            {currentActivityIndex + 1} of {activities.length}
          </div>
        )}
      </div>

      {/* Celebration modal */}
      <CelebrationModal
        isOpen={showCelebration}
        xpEarned={xpEarned}
        message="Lesson Complete!"
        onClose={handleCelebrationClose}
      />
    </div>
  );
}
