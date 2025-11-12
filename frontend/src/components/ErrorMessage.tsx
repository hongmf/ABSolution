import type { ApiError } from '../types';

interface ErrorMessageProps {
  error: ApiError;
  onRetry?: () => void;
}

export function ErrorMessage({ error, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-message">
      <div className="error-message__icon">⚠️</div>
      <div className="error-message__content">
        <h3>Error Loading Data</h3>
        <p>{error.message}</p>
        {error.code && <p className="error-code">Error Code: {error.code}</p>}
        {error.details && (
          <details>
            <summary>Technical Details</summary>
            <pre>{JSON.stringify(error.details, null, 2)}</pre>
          </details>
        )}
      </div>
      {onRetry && (
        <button className="error-message__retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
