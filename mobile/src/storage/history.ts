/**
 * Local SQLite history (expo-sqlite, async API). Offline-first: every
 * operation is local, no server history, no accounts.
 *
 * Schema v1 — one table, versioned via `PRAGMA user_version` so future
 * milestones can migrate without wiping user data:
 *
 *   calculations(
 *     id TEXT PRIMARY KEY,            -- stable local id (timestamp + random)
 *     image_uri TEXT NULL,            -- file URI only, never binary data
 *     original_latex TEXT NOT NULL,   -- backend prediction (may be '')
 *     corrected_expression TEXT NOT NULL,
 *     operation TEXT NOT NULL,        -- 'evaluate' | 'simplify' | 'solve:x'
 *     result TEXT NOT NULL,           -- display string
 *     created_at TEXT NOT NULL,       -- ISO 8601
 *     model_id TEXT NULL              -- e.g. 'posformer-crohme' when known
 *   )
 */

import * as SQLite from 'expo-sqlite';

export interface HistoryRecord {
  id: string;
  imageUri: string | null;
  originalLatex: string;
  correctedExpression: string;
  operation: string;
  result: string;
  createdAt: string;
  modelId: string | null;
}

const DB_NAME = 'eigen.db';
const SCHEMA_VERSION = 1;

let db: SQLite.SQLiteDatabase | null = null;

async function getDb(): Promise<SQLite.SQLiteDatabase> {
  if (db) return db;
  db = await SQLite.openDatabaseAsync(DB_NAME);
  await db.execAsync('PRAGMA journal_mode = WAL;');
  const row = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version;');
  const version = row?.user_version ?? 0;
  if (version < 1) {
    await db.execAsync(
      `CREATE TABLE IF NOT EXISTS calculations (
        id TEXT PRIMARY KEY,
        image_uri TEXT NULL,
        original_latex TEXT NOT NULL,
        corrected_expression TEXT NOT NULL,
        operation TEXT NOT NULL,
        result TEXT NOT NULL,
        created_at TEXT NOT NULL,
        model_id TEXT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_calculations_created
        ON calculations (created_at DESC);`,
    );
    await db.execAsync(`PRAGMA user_version = ${SCHEMA_VERSION};`);
  }
  // Future migrations: `if (version < 2) { ... }` — never drop user data.
  return db;
}

function rowToRecord(r: {
  id: string;
  image_uri: string | null;
  original_latex: string;
  corrected_expression: string;
  operation: string;
  result: string;
  created_at: string;
  model_id: string | null;
}): HistoryRecord {
  return {
    id: r.id,
    imageUri: r.image_uri,
    originalLatex: r.original_latex,
    correctedExpression: r.corrected_expression,
    operation: r.operation,
    result: r.result,
    createdAt: r.created_at,
    modelId: r.model_id,
  };
}

export function makeId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export async function saveCalculation(
  input: Omit<HistoryRecord, 'id' | 'createdAt'> & { id?: string; createdAt?: string },
): Promise<HistoryRecord> {
  const database = await getDb();
  const rec: HistoryRecord = {
    imageUri: input.imageUri,
    originalLatex: input.originalLatex,
    correctedExpression: input.correctedExpression,
    operation: input.operation,
    result: input.result,
    modelId: input.modelId,
    id: input.id ?? makeId(),
    createdAt: input.createdAt ?? new Date().toISOString(),
  };
  await database.runAsync(
    `INSERT OR REPLACE INTO calculations
      (id, image_uri, original_latex, corrected_expression, operation, result, created_at, model_id)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?);`,
    [
      rec.id,
      rec.imageUri,
      rec.originalLatex,
      rec.correctedExpression,
      rec.operation,
      rec.result,
      rec.createdAt,
      rec.modelId,
    ],
  );
  return rec;
}

export async function listCalculations(limit = 50): Promise<HistoryRecord[]> {
  const database = await getDb();
  const rows = await database.getAllAsync<{
    id: string;
    image_uri: string | null;
    original_latex: string;
    corrected_expression: string;
    operation: string;
    result: string;
    created_at: string;
    model_id: string | null;
  }>(`SELECT * FROM calculations ORDER BY created_at DESC LIMIT ?;`, [limit]);
  return rows.map(rowToRecord);
}

export async function getCalculation(id: string): Promise<HistoryRecord | null> {
  const database = await getDb();
  const row = await database.getFirstAsync<{
    id: string;
    image_uri: string | null;
    original_latex: string;
    corrected_expression: string;
    operation: string;
    result: string;
    created_at: string;
    model_id: string | null;
  }>(`SELECT * FROM calculations WHERE id = ?;`, [id]);
  return row ? rowToRecord(row) : null;
}

export async function deleteCalculation(id: string): Promise<void> {
  const database = await getDb();
  await database.runAsync(`DELETE FROM calculations WHERE id = ?;`, [id]);
}

export async function clearCalculations(): Promise<void> {
  const database = await getDb();
  await database.runAsync(`DELETE FROM calculations;`);
}
