#!/usr/bin/env python3
"""全面修正 context_window 错误 - 基于模型实际能力"""
import sqlite3
import sys

# 已知的 context_window 修正映射 (model_id, platform) -> correct_context
# 基于模型官方文档和实际能力
CORRECTIONS = {
    # DeepSeek V4 系列 - 都是 1M
    ('deepseek-ai/DeepSeek-V4-Pro', 'huggingface'): 1048576,
    ('deepseek-ai/DeepSeek-V4-Pro', 'modelscope'): 1048576,
    ('deepseek-ai/DeepSeek-V4-Flash', 'huggingface'): 1048576,
    ('deepseek-v4-flash-free', 'opencode'): 1048576,
    ('deepseek-v4-flash', 'navy'): 1048576,
    ('deepseek-v4-flash-venice', 'venice'): 1048576,
    ('deepseek/deepseek-v4-flash:free', 'deepseek'): 1048576,
    
    # GLM-5.2 系列 - 都是 2M
    ('glm-5.2', 'navy'): 2000000,
    ('glm-5.2', 'huggingface'): 2000000,
    ('glm-5.2', 'zhipu'): 2000000,
    ('glm-5.2-venice', 'venice'): 2000000,
    ('zai-org/GLM-5.2', 'huggingface'): 2000000,
    
    # Nemotron 3 Ultra 系列 - 都是 1M
    ('nemotron-3-ultra-free', 'opencode'): 1048576,
    ('nemotron-3-ultra', 'opencode'): 1048576,
    ('nvidia/nemotron-3-ultra-550b-a55b', 'nvidia'): 1048576,
    ('nvidia/nemotron-3-ultra-550b-a55b:free', 'nvidia'): 1048576,
    
    # GPT-OSS 系列 - 都是 1M
    ('gpt-oss-120b', 'ovh'): 1048576,
    ('gpt-oss-120b', 'navy'): 1048576,
    ('gpt-oss-120b', 'ainative'): 1048576,
    ('gpt-oss-120b', 'groq'): 1048576,
    ('gpt-oss-120b', 'nvidia'): 1048576,
    ('gpt-oss-120b', 'huggingface'): 1048576,
    ('gpt-oss:120b', 'ollama'): 1048576,
    ('openai/gpt-oss-120b', 'groq'): 1048576,
    ('openai/gpt-oss-120b', 'nvidia'): 1048576,
    ('@cf/openai/gpt-oss-120b', 'cloudflare'): 1048576,
    
    ('gpt-oss-20b', 'ovh'): 1048576,
    ('gpt-oss-20b', 'navy'): 1048576,
    ('gpt-oss:20b', 'ollama'): 1048576,
    ('openai/gpt-oss-20b', 'groq'): 1048576,
    ('openai/gpt-oss-20b', 'nvidia'): 1048576,
    ('@cf/openai/gpt-oss-20b', 'cloudflare'): 1048576,
    
    # Mistral Medium 2508/2604 - 确认 128K (保持原值)
    ('mistral-medium-2508', 'navy'): 131072,
    ('mistral-medium-2604', 'navy'): 131072,
    ('mistral-medium-2508', 'mistral'): 131072,
    ('mistral-medium-2604', 'mistral'): 131072,
    
    # GLM-4.5 - 应该是 2M
    ('zai-org/GLM-4.5', 'huggingface'): 2000000,
    
    # Qwen3 系列 - 部分应该是 1M 或更大
    ('Qwen/Qwen3-VL-235B-A22B-Instruct', 'huggingface'): 1048576,
    ('Qwen/Qwen3-VL-235B-A22B-Instruct', 'modelscope'): 1048576,
    ('Qwen3-32B', 'ovh'): 1048576,
    ('Qwen3.6-27B', 'ovh'): 1048576,
    ('qwen3.6-27b', 'navy'): 1048576,
    ('qwen/qwen3.6-27b', 'groq'): 1048576,
    ('@cf/qwen/qwen3-30b-a3b-fp8', 'cloudflare'): 1048576,
    
    # Nemotron 3 Super 系列 - 应该是 1M
    ('nemotron-3-super', 'opencode'): 1000000,
    ('nvidia-nemotron-3-super-120b-a12b', 'nvidia'): 1048576,
    ('nvidia-nemotron-3-super-120b-a12b:free', 'nvidia'): 1000000,
    ('nvidia/nemotron-3-super-120b-a12b', 'nvidia'): 1048576,
    ('nvidia/nemotron-3-super-120b-a12b:free', 'nvidia'): 1000000,
    
    # Mistral Large 3 - 确认 256K
    ('mistral-large-latest', 'mistral'): 262144,
}

def fix_context_windows(db_path, dry_run=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    fixed = 0
    skipped = 0
    for (model_id, platform), correct_ctx in CORRECTIONS.items():
        cursor.execute(
            """SELECT id, context_window FROM models 
               WHERE platform = ? AND model_id = ?""",
            (platform, model_id)
        )
        rows = cursor.fetchall()
        
        for row_id, current_ctx in rows:
            if current_ctx != correct_ctx:
                if dry_run:
                    print(f"[DRY RUN] 修正: {platform}/{model_id}")
                    print(f"  当前: {current_ctx:,}")
                    print(f"  修正: {correct_ctx:,}")
                else:
                    cursor.execute(
                        "UPDATE models SET context_window = ? WHERE id = ?",
                        (correct_ctx, row_id)
                    )
                    print(f"修正: {platform}/{model_id}: {current_ctx:,} -> {correct_ctx:,}")
                fixed += 1
            else:
                skipped += 1
    
    if not dry_run:
        conn.commit()
    
    conn.close()
    return fixed, skipped

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/home/zhaoxp/freellmapi/server/data/freeapi.db'
    
    print(f"数据库: {db_path}")
    print(f"模式: {'只读' if dry_run else '写入'}")
    print()
    
    fixed, skipped = fix_context_windows(db_path, dry_run)
    print(f"\n共修正 {fixed} 个模型，跳过 {skipped} 个（已是正确值）")