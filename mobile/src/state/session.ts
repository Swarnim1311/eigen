/**
 * In-memory working session for one calculation flow.
 * Router params stay tiny (ids only); image URIs and LaTeX travel here.
 * History persistence lives in `src/storage/history.ts` — this store is
 * intentionally NOT persisted (a killed app restarts from Home/History).
 */

export interface SessionState {
  imageUri: string | null;
  /** Exact LaTeX returned by the backend (never edited in place). */
  originalLatex: string | null;
  /** User-corrected, editable expression (ASCII grammar or LaTeX subset). */
  corrected: string;
  beamScore: number | null;
  modelId: string | null;
  reopenedId: string | null;
}

const fresh: SessionState = {
  imageUri: null,
  originalLatex: null,
  corrected: '',
  beamScore: null,
  modelId: null,
  reopenedId: null,
};

let current: SessionState = { ...fresh };

export function getSession(): SessionState {
  return current;
}

export function setSession(patch: Partial<SessionState>): SessionState {
  current = { ...current, ...patch };
  return current;
}

export function resetSession(): SessionState {
  current = { ...fresh };
  return current;
}
