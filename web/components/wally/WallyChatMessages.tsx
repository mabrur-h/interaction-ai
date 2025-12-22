'use client';

import clsx from 'clsx';
import { RefObject } from 'react';
import { WallyAvatar } from './WallyOwl';
import type { ChatBubble } from '@/components/chat/types';

interface WallyChatMessagesProps {
  messages: ReadonlyArray<ChatBubble>;
  isWaitingForResponse: boolean;
  scrollContainerRef: RefObject<HTMLDivElement | null>;
  onScroll: () => void;
  childName?: string;
}

export function WallyChatMessages({
  messages,
  isWaitingForResponse,
  scrollContainerRef,
  onScroll,
  childName = 'friend',
}: WallyChatMessagesProps) {
  return (
    <div
      ref={scrollContainerRef}
      onScroll={onScroll}
      className="flex h-[65vh] flex-col gap-3 overflow-y-auto p-4"
    >
      {messages.length === 0 && <WallyEmptyState childName={childName} />}

      {messages.map((message, index) => {
        const isUser = message.role === 'user';
        const isDraft = message.role === 'draft';
        const next = messages[index + 1];
        const tail = !next || next.role !== message.role;
        const isFirst = index === 0 || messages[index - 1]?.role !== message.role;

        return (
          <div
            key={message.id}
            className={clsx('flex items-end gap-2', isUser ? 'justify-end' : 'justify-start')}
          >
            {/* Wally avatar for assistant messages */}
            {!isUser && isFirst && <WallyAvatar className="w-10 h-10 flex-shrink-0" />}
            {!isUser && !isFirst && <div className="w-10 flex-shrink-0" />}

            <div
              className={clsx(
                isUser ? 'bubble-kid' : 'bubble-wally',
                tail ? (isUser ? 'rounded-br-lg' : 'rounded-bl-lg') : '',
                isDraft && 'whitespace-pre-wrap'
              )}
            >
              <span className={isDraft ? 'block whitespace-pre-wrap' : 'whitespace-pre-wrap'}>
                {message.text}
              </span>
            </div>
          </div>
        );
      })}

      {isWaitingForResponse && <WallyTypingIndicator />}
    </div>
  );
}

function WallyTypingIndicator() {
  return (
    <div className="flex items-end gap-2 justify-start">
      <WallyAvatar className="w-10 h-10 flex-shrink-0 animate-wiggle" />
      <div className="bubble-wally rounded-bl-lg">
        <div className="flex items-center space-x-1.5 px-2">
          <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-purple-200 [animation-delay:-0.3s]"></div>
          <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-purple-200 [animation-delay:-0.15s]"></div>
          <div className="h-2.5 w-2.5 animate-bounce rounded-full bg-purple-200"></div>
        </div>
      </div>
    </div>
  );
}

function WallyEmptyState({ childName }: { childName: string }) {
  return (
    <div className="mx-auto my-8 max-w-sm text-center">
      <div className="mb-4 text-6xl animate-bounce-in">🦉</div>
      <h2 className="mb-3 text-2xl font-bold text-violet-700">
        Hoo-hoo, {childName}!
      </h2>
      <p className="text-lg text-gray-600 mb-4">
        I&apos;m Wally the Owl, your money helper!
      </p>
      <div className="bg-violet-50 rounded-2xl p-4 text-left">
        <p className="text-gray-700 font-medium mb-2">Try asking me:</p>
        <ul className="space-y-2 text-gray-600">
          <li className="flex items-center gap-2">
            <span className="text-xl">💰</span>
            <span>&quot;How much money do I have?&quot;</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-xl">🐷</span>
            <span>&quot;I want to save for a toy&quot;</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-xl">📊</span>
            <span>&quot;What did I spend this week?&quot;</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default WallyChatMessages;
