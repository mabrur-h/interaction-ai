'use client';

import { KeyboardEvent, ChangeEvent } from 'react';

interface WallyChatInputProps {
  value: string;
  canSubmit: boolean;
  placeholder?: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function WallyChatInput({
  value,
  canSubmit,
  placeholder = 'Ask Wally something...',
  onChange,
  onSubmit,
}: WallyChatInputProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && canSubmit) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="flex gap-3">
      <input
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="input-wally flex-1"
        autoComplete="off"
      />
      <button
        onClick={onSubmit}
        disabled={!canSubmit}
        className="btn-wally px-6"
        aria-label="Send message"
      >
        <span className="text-xl">🚀</span>
        <span className="ml-2 hidden sm:inline">Send</span>
      </button>
    </div>
  );
}

export default WallyChatInput;
