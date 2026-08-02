import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { initDb, getDb, setSetting } from '../../db/index.js';
import { resolveRoutingChain } from '../../services/router.ts';
import type { Db } from '../../db/index.js';
import { tierValue } from '../../services/scoring.ts';

// Helper to insert a model and link it via fallback_config (for active chain)
// Returns the model_db_id
function addModelToFallback(db: Db, modelId: string, sizeLabel: string, priority: number): number {
  const insertModel = db.prepare(`
    INSERT INTO models (
      platform, model_id, display_name, intelligence_rank, speed_rank, size_label,
      rpm_limit, rpd_limit, tpm_limit, tpd_limit, monthly_token_budget,
      context_window, enabled, supports_vision, supports_tools
    ) VALUES (
      'test', ?, 'Test Model', 0, 0, ?, NULL, NULL, NULL, NULL, '~1M', 128000, 1, 0, 0
    )
  `);
  const info = insertModel.run(modelId, sizeLabel);
  const modelIdNum = Number(info.lastInsertRowid);

  // Link into fallback_config so it appears in getActiveChain
  const insertFallback = db.prepare(`
    INSERT INTO fallback_config (model_db_id, priority, enabled)
    VALUES (?, ?, 1)
  `);
  insertFallback.run(modelIdNum, priority);

  return modelIdNum;
}

// Helper to insert a model and link it via auxiliary_config for a given task type
function addModelToTask(
  db: Db,
  modelId: string,
  sizeLabel: string,
  priority: number,
  taskType: string
): number {
  const insertModel = db.prepare(`
    INSERT INTO models (
      platform, model_id, display_name, intelligence_rank, speed_rank, size_label,
      rpm_limit, rpd_limit, tpm_limit, tpd_limit, monthly_token_budget,
      context_window, enabled, supports_vision, supports_tools
    ) VALUES (
      'test', ?, 'Test Model', 0, 0, ?, NULL, NULL, NULL, NULL, '~1M', 128000, 1, 0, 0
    )
  `);
  const info = insertModel.run(modelId, sizeLabel);
  const modelIdNum = Number(info.lastInsertRowid);

  const insertAc = db.prepare(`
    INSERT INTO auxiliary_config (task_type, model_db_id, priority, enabled)
    VALUES (?, ?, ?, 1)
  `);
  insertAc.run(taskType, modelIdNum, priority);

  return modelIdNum;
}

describe('auto_min_tier floor guard', () => {
  beforeEach(() => {
    process.env.ENCRYPTION_KEY = '0'.repeat(64);
    initDb(':memory:');
    const db = getDb();
    // Clear tables in the correct order to avoid foreign key constraints
    db.prepare('DELETE FROM settings').run();
    db.prepare('DELETE FROM auxiliary_config').run();
    db.prepare('DELETE FROM fallback_config').run();
    db.prepare('DELETE FROM models').run();
    // Ensure auto_min_tier setting exists (default Large)
    setSetting('auto_min_tier', 'Large');
  });

  afterEach(() => {
    // Cleanup handled by re-initing DB each test
  });

  describe('auto (bare model name or undefined)', () => {
    it('filters out models below the min tier', () => {
      const db = getDb();
      // Add one Large (should pass) and two Small (should be filtered)
      addModelToFallback(db, 'test_large', 'Large', 10);
      addModelToFallback(db, 'test_small1', 'Small', 20);
      addModelToFallback(db, 'test_small2', 'Small', 30);

      const res = resolveRoutingChain(undefined);
      // Expect that the chain contains the large model and not the small models
      const modelIds = res.chain.map(c => c.model_id);
      expect(modelIds).toContain('test_large');
      expect(modelIds).not.toContain('test_small1');
      expect(modelIds).not.toContain('test_small2');
      // Additionally, all models in chain should have size_label >= Large
      expect(res.chain.every(c => 
        (c.size_label === 'Frontier' || c.size_label === 'Large')
      )).toBe(true);
    });

    it('throws when no models meet the min tier', () => {
      const db = getDb();
      // Only Small and Medium models
      addModelToFallback(db, 'test_medium', 'Medium', 10);
      addModelToFallback(db, 'test_small', 'Small', 20);

      expect(() => resolveRoutingChain(undefined)).toThrowError(
        /No models above auto_min_tier=Large/
      );
    });

    it('respects custom min tier setting', () => {
      const db = getDb();
      setSetting('auto_min_tier', 'Frontier');
      addModelToFallback(db, 'test_frontier', 'Frontier', 10);
      addModelToFallback(db, 'test_large', 'Large', 20);

      const res = resolveRoutingChain(undefined);
      expect(res.chain.length).toBe(1);
      expect(res.chain[0].model_id).toBe('test_frontier');
      expect(res.chain[0].size_label).toBe('Frontier');
    });
  });

  describe('auto:smart / auto:fast / auto:cheap / auto:reliable (global sort)', () => {
    it.each([
      ['auto:smart'],
      ['auto:fast'],
      ['auto:cheap'],
      ['auto:reliable'],
    ])('filters out models below the min tier for %s', (modelString) => {
      const db = getDb();
      addModelToFallback(db, 'test_large', 'Large', 10);
      addModelToFallback(db, 'test_small', 'Small', 20);

      const res = resolveRoutingChain(modelString);
      expect(res.chain.length).toBe(1);
      expect(res.chain.map(c => c.model_id)).toContain('test_large');
      expect(res.chain.map(c => c.model_id)).not.toContain('test_small');
      expect(res.chain.every(c => 
        (c.size_label === 'Frontier' || c.size_label === 'Large')
      )).toBe(true);
    });

    it.each([
      ['auto:smart'],
      ['auto:fast'],
      ['auto:cheap'],
      ['auto:reliable'],
    ])('throws when no models meet the min tier for %s', (modelString) => {
      const db = getDb();
      addModelToFallback(db, 'test_medium', 'Medium', 10);
      addModelToFallback(db, 'test_small', 'Small', 20);

      expect(() => resolveRoutingChain(modelString)).toThrowError(
        /No enabled models available for global sort/
      );
    });
  });

  describe('auto:<task_type> (task_type chains from auxiliary_config)', () => {
    it('ignores auto_min_tier and returns all enabled models for the task', () => {
      const db = getDb();
      // Set a high min tier that would filter out Medium/Small in active chain
      setSetting('auto_min_tier', 'Large');

      // Add a Small model to the 'vision' task
      addModelToTask(db, 'vis_small', 'Small', 5, 'vision');
      // Add a Medium model to the same task (should still appear)
      addModelToTask(db, 'vis_medium', 'Medium', 10, 'vision');

      const res = resolveRoutingChain('auto:vision');
      expect(res.chain.length).toBe(2);
      const modelIds = res.chain.map(c => c.model_id);
      expect(modelIds).toContain('vis_small');
      expect(modelIds).toContain('vis_medium');
      // The size_labels should be Small and Medium (both below Large) but still present
      const labels = new Set(res.chain.map(c => c.size_label));
      expect(labels.has('Small')).toBe(true);
      expect(labels.has('Medium')).toBe(true);
    });

    it('still returns empty if no models are configured for the task', () => {
      const db = getDb();
      setSetting('auto_min_tier', 'Large');
      // No entries in auxiliary_config for 'vision'
      expect(() => resolveRoutingChain('auto:vision')).toThrowError(
        /Task type 'vision' has no enabled models/
      );
    });
  });
});