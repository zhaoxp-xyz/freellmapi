#!/usr/bin/env python3
"""修正新插入模型的 intelligence_rank 和 context_window"""

import sqlite3
import sys

# 手动配置的模型属性 (platform, model_id, intelligence_rank, context_window)
# 基于模型命名约定推断
UPDATES = [
    # mistral
    ('mistral', 'mistral-large-2512', 14, 262144),
    ('mistral', 'mistral-medium', 14, 131072),
    ('mistral', 'mistral-medium-2505', 14, 131072),
    ('mistral', 'mistral-medium-2508', 14, 131072),
    ('mistral', 'mistral-medium-2604', 14, 131072),
    ('mistral', 'mistral-medium-3', 14, 131072),
    ('mistral', 'mistral-medium-3-5', 14, 262144),
    ('mistral', 'mistral-medium-3.5', 14, 262144),
    ('mistral', 'mistral-small-2603', 14, 262144),
    ('mistral', 'mistral-vibe-cli-latest', 14, 131072),
    ('mistral', 'mistral-vibe-cli-with-tools', 14, 131072),
    ('mistral', 'codestral-2508', 16, 32000),
    ('mistral', 'devstral-2512', 16, 32000),
    ('mistral', 'mistral-code-fim-latest', 16, 32000),
    ('mistral', 'ministral-14b-2512', 20, 131072),
    ('mistral', 'ministral-3b-2512', 35, 32768),
    ('mistral', 'ministral-3b-latest', 35, 32768),
    ('mistral', 'ministral-8b-2512', 25, 131072),
    ('mistral', 'voxtral-small-2507', 35, 32768),
    ('mistral', 'voxtral-small-latest', 35, 32768),
    # nvidia - larger models
    ('nvidia', 'meta/llama-3.1-70b-instruct', 10, 131072),
    ('nvidia', 'meta/llama-3.1-8b-instruct', 28, 131072),
    ('nvidia', 'meta/llama-3.2-11b-vision-instruct', 25, 131072),
    ('nvidia', 'meta/llama-3.2-1b-instruct', 45, 8192),
    ('nvidia', 'meta/muse-glimmer-30b', 18, 131072),
    ('nvidia', 'mistralai/mistral-nemotron', 18, 131072),
    ('nvidia', 'moonshotai/kimi-k3', 8, 200000),
    # nemotron family
    ('nvidia', 'nvidia/llama-3.3-nemotron-super-49b-v1', 10, 131072),
    ('nvidia', 'nvidia/llama-3.3-nemotron-super-49b-v1.5', 10, 131072),
    ('nvidia', 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning', 20, 131072),
    ('nvidia', 'nvidia/nemotron-3.5-lightning-30b-a3b', 20, 131072),
    ('nvidia', 'nvidia/nemotron-mini-4b-instruct', 35, 131072),
    ('nvidia', 'nvidia/nemotron-nano-12b-v2-vl', 35, 131072),
    ('nvidia', 'nvidia/nvidia-nemotron-nano-9b-v2', 40, 131072),
    # safety/guard models
    ('nvidia', 'nvidia/llama-3.1-nemoguard-8b-content-safety', 60, 8192),
    ('nvidia', 'nvidia/llama-3.1-nemoguard-8b-topic-control', 60, 8192),
    ('nvidia', 'nvidia/llama-3.1-nemotron-nano-vl-8b-v1', 45, 131072),
    ('nvidia', 'nvidia/llama-3.1-nemotron-safety-guard-8b-v3', 60, 8192),
    # translation
    ('nvidia', 'nvidia/riva-translate-4b-instruct-v1.1', 55, 4096),
    ('nvidia', 'nvidia/riva-translate-4b-instruct-v2', 55, 4096),
    # deepseek
    ('nvidia', 'deepseek-ai/deepseek-v4-flash-0731', 4, 131072),
    # stepfun
    ('nvidia', 'stepfun-ai/step-3.7-flash', 12, 262144),
    # thinkingmachines
    ('nvidia', 'thinkingmachines/inkling', 25, 131072),
    # nara
    ('nara', 'muse-spark-1.2-contributor-free', 35, 131072),
    ('nara', 'ox-alpha', 30, 131072),
    ('nara', 'ox-alpha-bynara', 30, 131072),
    ('nara', 'qwen-3.8-max-free', 10, 131072),
    ('nara', 'stepfun-3.7-flash', 12, 262144),
    # agnes
    ('agnes', 'agnes-2.5-pro', 10, 131072),
    ('agnes', 'agnes-2.5-pro-alpha', 10, 131072),
    # opencode
    ('opencode', 'nemotron-3.5-lightning-free', 20, 131072),
    ('opencode', 'x-preview-f-free', 30, 131072),
    # openrouter
    ('openrouter', 'stealth/ox-alpha', 30, 131072),
]

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <db_path> [--dry-run]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    updated = 0
    not_found = []
    
    for platform, model_id, rank, ctx in UPDATES:
        # Find the model
        cur.execute("SELECT id FROM models WHERE platform=? AND model_id=?", (platform, model_id))
        row = cur.fetchone()
        if not row:
            not_found.append(f"{platform}/{model_id}")
            continue
        
        model_id_db = row[0]
        cur.execute("UPDATE models SET intelligence_rank=?, context_window=? WHERE id=?", (rank, ctx, model_id_db))
        updated += 1
        if dry_run:
            print(f"  [DRY] {platform}/{model_id}: rank={rank}, ctx={ctx}")
        else:
            print(f"  [OK] {platform}/{model_id}: rank={rank}, ctx={ctx}")
    
    conn.commit()
    conn.close()
    
    print(f"\nUpdated: {updated} models")
    if not_found:
        print(f"Not found: {len(not_found)} models")
        for m in not_found:
            print(f"  - {m}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
