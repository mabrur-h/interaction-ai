interface ChatHeaderProps {
  onOpenSettings: () => void;
  onClearHistory: () => void;
  onLogout: () => void;
}

export function ChatHeader({ onOpenSettings, onClearHistory, onLogout }: ChatHeaderProps) {
  return (
    <header className="mb-4 flex items-center justify-between">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold">OpenPoke 🌴</h1>
      </div>
      <div className="flex items-center gap-2">
        <button
          className="rounded-md border border-gray-200 px-3 py-2 text-sm hover:bg-gray-50"
          onClick={onOpenSettings}
        >
          Settings
        </button>
        <button
          className="rounded-md border border-gray-200 px-3 py-2 text-sm hover:bg-gray-50"
          onClick={onClearHistory}
        >
          Clear
        </button>
        <button
          className="rounded-md border border-red-200 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
          onClick={onLogout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}
