'use client';

interface WallyOwlProps {
  className?: string;
  mood?: 'happy' | 'thinking' | 'excited' | 'default';
}

export function WallyOwl({ className = '', mood = 'default' }: WallyOwlProps) {
  // Mood-based adjustments
  const eyeSparkle = mood === 'excited' || mood === 'happy';
  const wingAnimation = mood === 'excited' ? 'animate-wiggle' : '';

  return (
    <svg
      className={`${className} ${wingAnimation}`}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Body */}
      <ellipse cx="50" cy="60" rx="35" ry="30" fill="#8B5CF6" />
      {/* Belly */}
      <ellipse cx="50" cy="65" rx="20" ry="18" fill="#DDD6FE" />
      {/* Head */}
      <circle cx="50" cy="35" r="28" fill="#8B5CF6" />
      {/* Face */}
      <ellipse cx="50" cy="40" rx="18" ry="15" fill="#DDD6FE" />
      {/* Left eye */}
      <circle cx="40" cy="35" r="10" fill="white" />
      <circle cx="42" cy="35" r="5" fill="#1F2937" />
      <circle cx="43" cy="33" r="2" fill="white" />
      {eyeSparkle && <circle cx="38" cy="31" r="1.5" fill="#FCD34D" />}
      {/* Right eye */}
      <circle cx="60" cy="35" r="10" fill="white" />
      <circle cx="62" cy="35" r="5" fill="#1F2937" />
      <circle cx="63" cy="33" r="2" fill="white" />
      {eyeSparkle && <circle cx="58" cy="31" r="1.5" fill="#FCD34D" />}
      {/* Beak */}
      <path d="M45 45 L50 55 L55 45 Z" fill="#F97316" />
      {/* Left ear tuft */}
      <path d="M25 20 Q30 5 35 15 Q30 12 28 20 Z" fill="#8B5CF6" />
      {/* Right ear tuft */}
      <path d="M75 20 Q70 5 65 15 Q70 12 72 20 Z" fill="#8B5CF6" />
      {/* Wings */}
      <ellipse cx="20" cy="55" rx="10" ry="20" fill="#7C3AED" />
      <ellipse cx="80" cy="55" rx="10" ry="20" fill="#7C3AED" />
      {/* Feet */}
      <ellipse cx="40" cy="88" rx="8" ry="5" fill="#F97316" />
      <ellipse cx="60" cy="88" rx="8" ry="5" fill="#F97316" />
    </svg>
  );
}

// Small avatar version for chat bubbles
export function WallyAvatar({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-gradient-to-br from-violet-500 to-purple-700 rounded-full p-1 ${className}`}>
      <svg
        className="w-full h-full"
        viewBox="0 0 50 50"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Head */}
        <circle cx="25" cy="25" r="20" fill="#8B5CF6" />
        {/* Face */}
        <ellipse cx="25" cy="28" rx="12" ry="10" fill="#DDD6FE" />
        {/* Left eye */}
        <circle cx="19" cy="24" r="6" fill="white" />
        <circle cx="20" cy="24" r="3" fill="#1F2937" />
        <circle cx="21" cy="22" r="1" fill="white" />
        {/* Right eye */}
        <circle cx="31" cy="24" r="6" fill="white" />
        <circle cx="32" cy="24" r="3" fill="#1F2937" />
        <circle cx="33" cy="22" r="1" fill="white" />
        {/* Beak */}
        <path d="M22 32 L25 38 L28 32 Z" fill="#F97316" />
        {/* Ear tufts */}
        <path d="M10 12 Q14 4 17 10 Q14 8 12 12 Z" fill="#8B5CF6" />
        <path d="M40 12 Q36 4 33 10 Q36 8 38 12 Z" fill="#8B5CF6" />
      </svg>
    </div>
  );
}

export default WallyOwl;
