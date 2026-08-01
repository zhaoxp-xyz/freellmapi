import type { Db } from '../types.js';

/**
 * Harden auxiliary_config: add UNIQUE(task_type, model_db_id) so the
 * routes/auxiliary.ts add endpoint's ON CONFLICT upsert actually works.
 * Also add an index on task_type for chain lookups.
 * SQLite can't ALTER TABLE ADD CONSTRAINT — rebuild the table.
 */
export function up(db: Db): void {
  // 1. dedupe existing rows keeping the lowest id (and its priority)
  db.prepare(`
    DELETE FROM auxiliary_config
    WHERE id NOT IN (
      SELECT MIN(id) FROM auxiliary_config GROUP BY task_type, model_db_id
    )
  `).run();

  // 2. rebuild with the UNIQUE constraint
  db.exec(`
    CREATE TABLE auxiliary_config_new (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_type TEXT NOT NULL,
      model_db_id INTEGER NOT NULL,
      priority INTEGER NOT NULL DEFAULT 0,
      enabled INTEGER NOT NULL DEFAULT 1,
      UNIQUE (task_type, model_db_id),
      FOREIGN KEY (model_db_id) REFERENCES models (id) ON DELETE CASCADE
    );
    INSERT INTO auxiliary_config_new (id, task_type, model_db_id, priority, enabled)
      SELECT id, task_type, model_db_id, priority, enabled FROM auxiliary_config;
    DROP TABLE auxiliary_config;
    ALTER TABLE auxiliary_config_new RENAME TO auxiliary_config;
    CREATE INDEX IF NOT EXISTS idx_auxiliary_task_type ON auxiliary_config (task_type);
  `);
}

export function down(db: Db): void {
  db.exec(`
    CREATE TABLE auxiliary_config_old (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_type TEXT NOT NULL,
      model_db_id INTEGER NOT NULL,
      priority INTEGER NOT NULL DEFAULT 0,
      enabled INTEGER NOT NULL DEFAULT 1,
      FOREIGN KEY (model_db_id) REFERENCES models (id) ON DELETE CASCADE
    );
    INSERT INTO auxiliary_config_old (id, task_type, model_db_id, priority, enabled)
      SELECT id, task_type, model_db_id, priority, enabled FROM auxiliary_config;
    DROP TABLE auxiliary_config;
    ALTER TABLE auxiliary_config_old RENAME TO auxiliary_config;
  `);
}
