#!/usr/bin/env python3
"""
apamc_catalog_merge.py — Merge APAMC test results into freellmapi catalog.

Strategy:
1. Exact match: catalog modelId == APAMC model name → use APAMC ok/fail directly
2. No match: preserve existing enabled state (conservative)
3. New models: APAMC has but catalog doesn't → insert with defaults
4. User-sourced models are NEVER touched

Usage:
  python3 apamc_catalog_merge.py [--db /path/to/freeapi.db] [--results /path/to/apamc/results] [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# APAMC platform name → freellmapi catalog platform name mapping
PLATFORM_MAP = {
    "google_gemini": "google",
    "groq": "groq",
    "nvidia": "nvidia",
    "mistral": "mistral",
    "openrouter": "openrouter",
    "zhipu": "zhipu",
    "opencode": "opencode",
    "agnes": "agnes",
    "nara": "nara",
    "bai": "bai",
    "tokenrouter": "tokenrouter",
}

# Default metadata for new models not in catalog
DEFAULT_INTELLIGENCE_RANK = 50
DEFAULT_SPEED_RANK = 10
DEFAULT_CONTEXT_WINDOW = 131072


def load_catalog(db_path: str) -> dict[str, Any]:
    """Load catalog_applied_json from settings table."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = 'catalog_applied_json'")
    row = cur.fetchone()
    conn.close()
    if not row:
        print("[ERROR] No catalog_applied_json found in settings", file=sys.stderr)
        sys.exit(1)
    return json.loads(row["value"])


def load_apamc_results(results_dir: str) -> dict[str, dict]:
    """Load all APAMC platform result files."""
    results_path = Path(results_dir)
    apamc_data: dict[str, dict] = {}
    for f in sorted(results_path.glob("*.json")):
        if f.stem in ("summary", "baseline") or f.stem.endswith("_models") or f.stem.endswith("_report"):
            continue
        try:
            data = json.loads(f.read_text())
            platform = data.get("platform", f.stem)
            apamc_data[platform] = {
                "ok": set(data.get("ok", [])),
                "fail": set(data.get("fail", [])),
                "total": data.get("total", 0),
                "tested_at": data.get("tested_at", ""),
            }
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] Failed to load {f}: {e}", file=sys.stderr)
    return apamc_data


def build_apamc_lookup(apamc_data: dict) -> dict[str, dict[str, set]]:
    """Build lookup: flm_platform -> {modelId: ok/fail set}."""
    lookup: dict[str, dict[str, set]] = {}
    for apamc_name, info in apamc_data.items():
        flm_name = PLATFORM_MAP.get(apamc_name)
        if not flm_name:
            continue
        if flm_name not in lookup:
            lookup[flm_name] = {"ok": set(), "fail": set()}
        lookup[flm_name]["ok"] |= info["ok"]
        lookup[flm_name]["fail"] |= info["fail"]
    return lookup


def merge_catalog(catalog: dict, apamc_lookup: dict) -> tuple[dict, dict]:
    """
    Merge APAMC results into catalog using exact modelId matching.
    Returns (merged_catalog, stats).
    """
    stats = {
        "models_updated": 0,
        "models_disabled": 0,
        "models_enabled": 0,
        "models_new": 0,
        "models_exact_match": 0,
        "models_no_match": 0,
        "platforms_covered": 0,
    }

    # Track which (platform, modelId) we've processed
    processed: set[tuple[str, str]] = set()

    # Merge existing models
    for model in catalog.get("models", []):
        plat = model["platform"]
        mid = model["modelId"]
        processed.add((plat, mid))

        # Skip if no APAMC data for this platform
        if plat not in apamc_lookup:
            stats["models_no_match"] += 1
            continue

        apamc = apamc_lookup[plat]
        if mid in apamc["fail"]:
            # APAMC says this model is DOWN → disable it
            if model.get("enabled", True):
                model["enabled"] = False
                stats["models_disabled"] += 1
                stats["models_updated"] += 1
                stats["models_exact_match"] += 1
        elif mid in apamc["ok"]:
            # APAMC says OK → ensure enabled
            if not model.get("enabled", True):
                model["enabled"] = True
                stats["models_enabled"] += 1
                stats["models_updated"] += 1
                stats["models_exact_match"] += 1
        else:
            # No match → preserve state
            stats["models_no_match"] += 1

    # Find new models in APAMC not in catalog
    for flm_plat, apamc in apamc_lookup.items():
        for mid in apamc["ok"]:
            if (flm_plat, mid) not in processed:
                # New model found! Add with defaults
                new_model = {
                    "platform": flm_plat,
                    "modelId": mid,
                    "displayName": mid,  # Will be refined later
                    "intelligenceRank": DEFAULT_INTELLIGENCE_RANK,
                    "speedRank": DEFAULT_SPEED_RANK,
                    "sizeLabel": "Unknown",
                    "limits": {"rpm": None, "rpd": None, "tpm": None, "tpd": None},
                    "monthlyTokenBudget": None,
                    "contextWindow": DEFAULT_CONTEXT_WINDOW,
                    "enabled": True,
                    "supportsVision": False,
                    "supportsTools": False,
                }
                catalog["models"].append(new_model)
                stats["models_new"] += 1
                processed.add((flm_plat, mid))

    stats["platforms_covered"] = len(apamc_lookup)
    return catalog, stats


def apply_to_db(db_path: str, catalog: dict) -> dict:
    """Apply merged catalog to the database (simplified applyCatalog logic)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    counts = {"updated": 0, "inserted": 0, "removed": 0}

    # Build set of (platform, modelId) in catalog
    in_catalog = set()
    for m in catalog.get("models", []):
        plat = m["platform"]
        mid = m["modelId"]
        in_catalog.add((plat, mid))

        enabled = 1 if m.get("enabled", True) else 0
        supports_vision = 1 if m.get("supportsVision", False) else 0
        supports_tools = 1 if m.get("supportsTools", False) else 0
        ctx = m.get("contextWindow")

        # Check if model exists
        cur.execute(
            "SELECT id, enabled, source FROM models WHERE platform = ? AND model_id = ?",
            (plat, mid),
        )
        row = cur.fetchone()

        if row:
            row_id, row_enabled, row_source = row
            # User-sourced models are never updated
            if row_source == "user":
                counts["updated"] += 1
                continue
            # Catalog disable wins; local disable also wins
            # If APAMC says fail (enabled=0), force disable
            # If APAMC says ok (enabled=1), preserve local setting
            new_enabled = enabled if enabled == 0 else row_enabled
            cur.execute(
                """UPDATE models SET
                    enabled = ?,
                    supports_vision = ?,
                    supports_tools = ?
                WHERE id = ?""",
                (new_enabled, supports_vision, supports_tools, row_id),
            )
            counts["updated"] += 1
        else:
            # New model — insert
            cur.execute(
                """INSERT INTO models
                    (platform, model_id, display_name, intelligence_rank, speed_rank,
                     size_label, rpm_limit, rpd_limit, tpm_limit, tpd_limit,
                     monthly_token_budget, context_window, enabled,
                     supports_vision, supports_tools, source)
                VALUES (?, ?, ?, ?, ?, '', NULL, NULL, NULL, NULL,
                        ?, ?, ?, ?, ?, 'catalog')""",
                (
                    plat,
                    mid,
                    m.get("displayName", mid),
                    m.get("intelligenceRank", DEFAULT_INTELLIGENCE_RANK),
                    m.get("speedRank", DEFAULT_SPEED_RANK),
                    m.get("monthlyTokenBudget") or "",
                    ctx or DEFAULT_CONTEXT_WINDOW,
                    enabled,
                    supports_vision,
                    supports_tools,
                ),
            )
            counts["inserted"] += 1

    # Remove models no longer in catalog (only catalog-sourced)
    cur.execute(
        "SELECT id, platform, model_id FROM models WHERE source = 'catalog'"
    )
    all_catalog_models = cur.fetchall()
    for row_id, plat, mid in all_catalog_models:
        if (plat, mid) not in in_catalog:
            # Delete fallback_config first (FK order)
            cur.execute(
                "DELETE FROM fallback_config WHERE model_db_id = ?", (row_id,)
            )
            cur.execute("DELETE FROM models WHERE id = ?", (row_id,))
            counts["removed"] += 1

    conn.commit()
    conn.close()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Merge APAMC results into freellmapi catalog")
    parser.add_argument("--db", default="~/freellmapi/server/data/freeapi.db",
                        help="Path to freeapi.db")
    parser.add_argument("--results", default="~/all-platforms-all-models-check/results",
                        help="Path to APAMC results directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without applying")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    results_dir = Path(args.results).expanduser()

    if not db_path.exists():
        print(f"[ERROR] DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    if not results_dir.exists():
        print(f"[ERROR] Results dir not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("APAMC → freellmapi Catalog Merge")
    print("=" * 60)
    print(f"DB: {db_path}")
    print(f"Results: {results_dir}")
    print()

    # Step 1: Load catalog
    print("[1/4] Loading catalog...")
    catalog = load_catalog(str(db_path))
    print(f"  Catalog version: {catalog.get('version', '?')}")
    print(f"  Models in catalog: {len(catalog.get('models', []))}")

    # Step 2: Load APAMC results
    print("[2/4] Loading APAMC results...")
    apamc_data = load_apamc_results(str(results_dir))
    apamc_lookup = build_apamc_lookup(apamc_data)
    print(f"  Platforms with results: {len(apamc_data)}")
    for plat, info in sorted(apamc_data.items()):
        flm_plat = PLATFORM_MAP.get(plat, "?")
        print(f"    {plat} → {flm_plat}: ok={len(info['ok'])} fail={len(info['fail'])}")

    # Step 3: Merge
    print("[3/4] Merging...")
    merged, merge_stats = merge_catalog(catalog, apamc_lookup)
    print(f"  Models updated: {merge_stats['models_updated']}")
    print(f"  Models disabled: {merge_stats['models_disabled']}")
    print(f"  Models enabled: {merge_stats['models_enabled']}")
    print(f"  New models: {merge_stats['models_new']}")
    print(f"  Exact matches: {merge_stats['models_exact_match']}")
    print(f"  No match (preserved): {merge_stats['models_no_match']}")
    print(f"  Platforms covered: {merge_stats['platforms_covered']}")

    # Step 4: Apply to DB
    print("[4/4] Applying to database...")
    if args.dry_run:
        print("  [DRY RUN] Skipping DB write")
    else:
        db_counts = apply_to_db(str(db_path), merged)
        print(f"  DB updated: {db_counts['updated']}")
        print(f"  DB inserted: {db_counts['inserted']}")
        print(f"  DB removed: {db_counts['removed']}")

        # Update catalog_applied_json in settings
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "UPDATE settings SET value = ? WHERE key = 'catalog_applied_json'",
            (json.dumps(merged, ensure_ascii=False),),
        )
        conn.execute(
            "UPDATE settings SET value = ? WHERE key = 'catalog_applied_version'",
            ("apamc-merge",),
        )
        conn.execute(
            "UPDATE settings SET value = ? WHERE key = 'catalog_applied_tier'",
            ("apamc",),
        )
        conn.execute(
            "UPDATE settings SET value = ? WHERE key = 'catalog_last_sync_ms'",
            (str(int(datetime.now(timezone.utc).timestamp() * 1000)),),
        )
        conn.commit()
        conn.close()
        print("  Catalog metadata updated in settings")

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
