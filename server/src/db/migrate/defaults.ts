import type Database from 'better-sqlite3';
import * as legacyBaseline from '../migrations/20260101_000000_legacy_baseline.js';
import * as customProviderModalities from '../migrations/20260627_000001_custom_provider_modalities.js';
import * as catalogModelState from '../migrations/20260627_000002_catalog_model_state.js';
import * as requestAggregates from '../migrations/20260628_120000_request_aggregates.js';
import * as githubGpt41Context from '../migrations/20260630_000001_github_gpt41_context.js';
import * as auxiliaryConfigUnique from '../migrations/20260801_080000_auxiliary_config_unique.js';
import * as auxiliaryConfig from '../migrations/20260731_120000_auxiliary_config.js';

export interface MigrationModule {
  up(db: Database.Database): void;
  down(db: Database.Database): void;
}

export interface DefaultMigration {
  filename: string;
  module: MigrationModule;
}

export const LEGACY_BASELINE_FILENAME = '20260101_000000_legacy_baseline.ts';
export const CUSTOM_PROVIDER_MODALITIES_FILENAME = '20260627_000001_custom_provider_modalities.ts';
export const CATALOG_MODEL_STATE_FILENAME = '20260627_000002_catalog_model_state.ts';
export const REQUEST_AGGREGATES_FILENAME = '20260628_120000_request_aggregates.ts';
export const GITHUB_GPT41_CONTEXT_FILENAME = '20260630_000001_github_gpt41_context.ts';
export const AUXILIARY_CONFIG_UNIQUE_FILENAME = '20260801_080000_auxiliary_config_unique.ts';
export const AUXILIARY_CONFIG_FILENAME = '20260731_120000_auxiliary_config.ts';

export const DEFAULT_MIGRATIONS: readonly DefaultMigration[] = [
  { filename: LEGACY_BASELINE_FILENAME, module: legacyBaseline },
  { filename: CUSTOM_PROVIDER_MODALITIES_FILENAME, module: customProviderModalities },
  { filename: CATALOG_MODEL_STATE_FILENAME, module: catalogModelState },
  { filename: REQUEST_AGGREGATES_FILENAME, module: requestAggregates },
  { filename: GITHUB_GPT41_CONTEXT_FILENAME, module: githubGpt41Context },
  { filename: AUXILIARY_CONFIG_UNIQUE_FILENAME, module: auxiliaryConfigUnique },
  { filename: AUXILIARY_CONFIG_FILENAME, module: auxiliaryConfig },
];
