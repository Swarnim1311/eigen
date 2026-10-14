/**
 * Centralized Eigen backend API client.
 *
 * Base URL comes from `EXPO_PUBLIC_API_URL` (see `mobile/.env.example`).
 * A physical phone cannot reach a Windows host via `localhost`, so the
 * default below only suits an emulator/web preview on the same machine;
 * on a device you MUST set the env var to the host's LAN address.
 *
 * All responses are validated before use — model/backend output is
 * untrusted input. Timeouts use AbortController (no fabricated progress).
 */

import Constants from 'expo-constants';

import type {
  ErrorBody,
  EvaluateRequest,
  EvaluateResponse,
  ReadyResponse,
  RecognizeResponse,
  SimplifyRequest,
  SimplifyResponse,
  SolveRequest,
  SolveResponse,
} from './types';

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

function resolveBaseUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) return fromEnv.trim().replace(/\/+$/, '');
  const host =
    typeof Constants.expoConfig?.hostUri === 'string'
      ? Constants.expoConfig.hostUri.split(':')[0]
      : null;
  if (__DEV__ && host) return `http://${host}:8000`;
  // Same-machine fallback (emulator preview / web). NOT reachable from a
  // physical phone — set EXPO_PUBLIC_API_URL in that case.
  return 'http://10.0.2.2:8000';
}

export function getApiBaseUrl(): string {
  return resolveBaseUrl();
}

/**
 * anySignal() with a manual fallback for JS runtimes that predate it.
 * Semantics match the native helper: the combined signal aborts when ANY
 * input aborts. Callers keep distinguishing timeout vs caller-cancel exactly
 * as before (via their own controller/signal state) — this only combines.
 */
function anySignal(signals: AbortSignal[]): AbortSignal {
  const nativeAny = (AbortSignal as unknown as {
    any?: (s: AbortSignal[]) => AbortSignal;
  }).any;
  if (typeof nativeAny === 'function') return nativeAny.call(AbortSignal, signals);
  const ctrl = new AbortController();
  for (const s of signals) {
    if (s.aborted) {
      ctrl.abort();
      break;
    }
    s.addEventListener('abort', () => ctrl.abort(), { once: true });
  }
  return ctrl.signal;
}

const MATH_TIMEOUT_MS = 30_000;
/** CPU inference averages ~29 s and peaks near 90 s (Phase-1 baseline). */
const RECOGNIZE_TIMEOUT_MS = 180_000;

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null;
}

function errorFromPayload(status: number, payload: unknown): ApiError {
  if (isRecord(payload) && isRecord(payload.error)) {
    const code = typeof payload.error.code === 'string' ? payload.error.code : 'unknown';
    const message =
      typeof payload.error.message === 'string' ? payload.error.message : 'Request failed.';
    return new ApiError(code, message, status);
  }
  return new ApiError('bad_response', `Server returned status ${status}.`, status);
}

async function postJson<T>(
  path: string,
  body: unknown,
  signal: AbortSignal,
  validate: (v: unknown) => v is T,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${resolveBaseUrl()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new ApiError('timeout', 'The request timed out. Your input was kept — try again.', 0);
    }
    throw new ApiError(
      'unreachable',
      'Backend unreachable. Check the API URL and that the server is running. Your input was kept.',
      0,
    );
  }
  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    throw new ApiError('bad_response', `Server returned status ${res.status}.`, res.status);
  }
  if (!res.ok) throw errorFromPayload(res.status, payload);
  if (!validate(payload)) throw new ApiError('bad_response', 'Unexpected server response shape.', res.status);
  return payload;
}

function withTimeout(ms: number): { signal: AbortSignal; cancel: () => void } {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  return { signal: c.signal, cancel: () => clearTimeout(t) };
}

// --- response validators (reject anything that does not match schemas.py) ---

function isEvaluateResponse(v: unknown): v is EvaluateResponse {
  return (
    isRecord(v) &&
    typeof v.result === 'string' &&
    (typeof v.decimal === 'number' || v.decimal === null) &&
    typeof v.expression === 'string'
  );
}

function isSimplifyResponse(v: unknown): v is SimplifyResponse {
  return isRecord(v) && typeof v.result === 'string' && typeof v.expression === 'string';
}

function isSolveResponse(v: unknown): v is SolveResponse {
  return (
    isRecord(v) &&
    typeof v.variable === 'string' &&
    Array.isArray(v.solutions) &&
    v.solutions.every((s) => typeof s === 'string') &&
    typeof v.count === 'number'
  );
}

function isRecognizeResponse(v: unknown): v is RecognizeResponse {
  return (
    isRecord(v) &&
    typeof v.latex === 'string' &&
    typeof v.beam_score === 'number' &&
    isRecord(v.model) &&
    typeof v.model.id === 'string' &&
    isRecord(v.math_parse) &&
    typeof v.math_parse.ok === 'boolean' &&
    typeof v.duration_s === 'number'
  );
}

function isReadyResponse(v: unknown): v is ReadyResponse {
  return isRecord(v) && v.api === 'ok' && isRecord(v.model) && typeof v.model.status === 'string';
}

// --- public API ---

export async function checkReady(signal?: AbortSignal): Promise<ReadyResponse> {
  const base = resolveBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}/api/v1/ready`, { signal });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw new ApiError(
      'unreachable',
      'Backend unreachable. Check the API URL and that the server is running.',
      0,
    );
  }
  const payload: unknown = await res.json().catch(() => null);
  if (!res.ok) throw errorFromPayload(res.status, payload);
  if (!isReadyResponse(payload)) throw new ApiError('bad_response', 'Unexpected readiness shape.', res.status);
  return payload;
}

export async function recognizeImage(
  imageUri: string,
  signal?: AbortSignal,
): Promise<RecognizeResponse> {
  const { signal: ts, cancel } = withTimeout(RECOGNIZE_TIMEOUT_MS);
  const combined = signal
    ? anySignal([signal, ts])
    : ts;
  try {
    const name = imageUri.split('/').pop()?.split('?')[0] || 'math.jpg';
    const lower = name.toLowerCase();
    const mime = lower.endsWith('.png')
      ? 'image/png'
      : lower.endsWith('.webp')
        ? 'image/webp'
        : 'image/jpeg';
    const form = new FormData();
    form.append('file', { uri: imageUri, name, type: mime } as unknown as Blob);
    let res: Response;
    try {
      res = await fetch(`${resolveBaseUrl()}/api/v1/recognize`, {
        method: 'POST',
        body: form,
        signal: combined,
      });
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        if (signal?.aborted) throw e; // caller-cancelled: propagate raw
        throw new ApiError('timeout', 'Recognition timed out. Your image was kept — try again.', 0);
      }
      throw new ApiError(
        'unreachable',
        'Backend unreachable. Check the API URL and that the server is running. Your image was kept.',
        0,
      );
    }
    const payload: unknown = await res.json().catch(() => null);
    if (!res.ok) throw errorFromPayload(res.status, payload);
    if (!isRecognizeResponse(payload)) {
      throw new ApiError('bad_response', 'Unexpected recognition response shape.', res.status);
    }
    return payload;
  } finally {
    cancel();
  }
}

export async function evaluateExpression(
  body: EvaluateRequest,
  signal?: AbortSignal,
): Promise<EvaluateResponse> {
  const { signal: ts, cancel } = withTimeout(MATH_TIMEOUT_MS);
  try {
    return await postJson(
      '/api/v1/math/evaluate',
      { expression: body.expression, variables: body.variables ?? {}, latex: body.latex ?? false },
      signal ? anySignal([signal, ts]) : ts,
      isEvaluateResponse,
    );
  } finally {
    cancel();
  }
}

export async function simplifyExpression(
  body: SimplifyRequest,
  signal?: AbortSignal,
): Promise<SimplifyResponse> {
  const { signal: ts, cancel } = withTimeout(MATH_TIMEOUT_MS);
  try {
    return await postJson(
      '/api/v1/math/simplify',
      { expression: body.expression, latex: body.latex ?? false },
      signal ? anySignal([signal, ts]) : ts,
      isSimplifyResponse,
    );
  } finally {
    cancel();
  }
}

export async function solveEquation(
  body: SolveRequest,
  signal?: AbortSignal,
): Promise<SolveResponse> {
  const { signal: ts, cancel } = withTimeout(MATH_TIMEOUT_MS);
  try {
    return await postJson(
      '/api/v1/math/solve',
      { equation: body.equation, variable: body.variable },
      signal ? anySignal([signal, ts]) : ts,
      isSolveResponse,
    );
  } finally {
    cancel();
  }
}

/** Human-readable hint per backend error code (codes come from the server). */
export function describeError(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof DOMException && e.name === 'AbortError') return 'Request cancelled.';
  return 'Something went wrong. Your input was kept — try again.';
}

export type { ErrorBody };
