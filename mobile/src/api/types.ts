/**
 * TypeScript mirrors of `backend/app/schemas.py` (Phase 2, API v0.2.0).
 * Field names match the backend exactly. Do NOT add fields the backend
 * does not return — responses are validated before use in `client.ts`.
 */

export interface ErrorDetail {
  code: string;
  message: string;
}

export interface ErrorBody {
  error: ErrorDetail;
}

export interface EvaluateRequest {
  expression: string;
  variables?: Record<string, number>;
  latex?: boolean;
}

export interface EvaluateResponse {
  result: string;
  decimal: number | null;
  expression: string;
}

export interface SimplifyRequest {
  expression: string;
  latex?: boolean;
}

export interface SimplifyResponse {
  result: string;
  expression: string;
}

export interface SolveRequest {
  equation: string;
  variable: string;
}

export interface SolveResponse {
  variable: string;
  solutions: string[];
  count: number;
}

export interface ModelInfo {
  id: string;
  experimental: true;
  baseline_note: string;
}

export interface MathParseStatus {
  ok: boolean;
  ascii: string | null;
  error: string | null;
}

export interface RecognizeResponse {
  latex: string;
  beam_score: number;
  model: ModelInfo;
  duration_s: number;
  math_parse: MathParseStatus;
}

export type ModelStatus =
  | 'ready'
  | 'loading'
  | 'standby'
  | 'unavailable'
  | 'unconfigured';

export interface ReadyResponse {
  api: 'ok';
  model: { status: ModelStatus; detail: string };
}
