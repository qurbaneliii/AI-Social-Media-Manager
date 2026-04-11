export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    trace_id: string;
    retryable: boolean;
  };
}
