#!/usr/bin/env python3
"""修正模型 context_window 错误"""
import sqlite3
import sys

# 已知的 context_window 修正映射 (platform/model_id -> correct_context)
CORRECTIONS = {
    # DeepSeek V4 Pro 应该是 1M
    ('deepseek-ai/DeepSeek-V4-Pro', 'huggingface'): 1048576,
    ('deepseek-ai/DeepSeek-V4-Pro', 'modelscope'): 1048576,
    
    # GLM-5.2 应该是 2M
    ('glm-5.2', 'navy'): 2000000,
    ('glm-5.2', 'huggingface'): 2000000,
    
    # Nemotron 3 Ultra Free 应该是 1M
    ('nemotron-3-ultra-free', 'opencode'): 1048576,
    
    # Mistral Medium 2508/2604 确认 128k
    ('mistral-medium-2508', 'navy'): 131072,
    ('mistral-medium-2604', 'navy'): 131072,
}

def fix_context_windows(db_path, dry_run=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    fixed = 0
    for (model_id, platform), correct_ctx in CORRECTIONS.items():
        # 查找匹配的模型
        cursor.execute(
            """SELECT id, context_window FROM models 
               WHERE platform = ? AND model_id = ?""",
            (platform, model_id)
        )
        rows = cursor.fetchall()
        
        for row_id, current_ctx in rows:
            if current_ctx != correct_ctx:
                print(f"修正: {platform}/{model_id}")
                print(f"  当前: {current_ctx:,}")
                print(f"  修正: {correct_ctx:,}")
                if not dry_run:
                    cursor.execute(
                        "UPDATE models SET context_window = ? WHERE id = ?",
                        (correct_ctx, row_id)
                    )
                    fixed += 1
                print()
    
    if not dry_run:
        conn.commit()
    
    conn.close()
    return fixed

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/home/zhaoxp/freellmapi/server/data/freeapi.db'
    
    print(f"数据库: {db_path}")
    print(f"模式: {'只读' if dry_run else '写入'}")
    print()
    
    fixed = fix_context_windows(db_path, dry_run)
    print(f"共修正 {fixed} 个模型")
