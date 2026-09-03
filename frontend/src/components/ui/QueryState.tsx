import type { ReactNode } from "react";
import { ErrorBanner } from "./ErrorBanner";
import { LoadingRow } from "./Spinner";

interface QueryStateProps<T> {
  isLoading: boolean;
  error: unknown;
  data: T | undefined;
  children: (data: T) => ReactNode;
  loadingLabel?: string;
}

export function QueryState<T>({
  isLoading,
  error,
  data,
  children,
  loadingLabel,
}: QueryStateProps<T>) {
  if (isLoading) return <LoadingRow label={loadingLabel} />;
  if (error) return <ErrorBanner error={error} />;
  if (data === undefined) return null;
  return <>{children(data)}</>;
}
