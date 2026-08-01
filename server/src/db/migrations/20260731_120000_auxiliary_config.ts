import type { Db } from '../types.js';

/**
 * Auxiliary chain management — per task_type model chains (vision, coding,
 * webextract, compression, ...). Each chain is an ordered list of model db
 * ids with priorities; router.ts consults these when a request names a
 * task type via the auto:<task_type> model alias.
 */
export function up(db: Db): void {
  db.prepare(`
    CREATE TABLE IF NOT EXISTS auxiliary_config (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_type TEXT NOT NULL,
      model_db_id INTEGER NOT NULL,
      priority INTEGER NOT NULL DEFAULT 0,
      enabled INTEGER NOT NULL DEFAULT 1,
      UNIQUE (task_type, model_db_id),
      FOREIGN KEY (model_db_id) REFERENCES models (id) ON DELETE CASCADE
    )
  `).run();
  db.prepare('CREATE INDEX IF NOT EXISTS idx_auxiliary_task_type ON auxiliary_config (task_type)').run();
}

export function down(db: Db): void {
  db.prepare('DROP TABLE IF EXISTS auxiliary_config').run();
}
