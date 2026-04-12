export function Loading() {
  return (
    <div className="flex flex-1 items-center justify-center py-24">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted-foreground/30 border-t-primary" />
    </div>
  );
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
      <p className="text-sm font-medium text-destructive">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs text-destructive underline transition-opacity hover:opacity-80"
        >
          try again
        </button>
      )}
    </div>
  );
}
