// 将 gpt4free (g4f) 接入 40 的 FreeLLMAPI —— 三表同插：api_keys + models + fallback_config
const D = require('better-sqlite3');
const crypto = require('/home/zhaoxp/freellmapi/server/dist/lib/crypto.js');
const db = new D('/home/zhaoxp/freellmapi/server/data/freeapi.db');
db.pragma('wal_checkpoint(TRUNCATE)');
crypto.initEncryptionKey(db);

const KEY = 'g4f-local-key';
const BASE = 'http://127.0.0.1:1337/v1';

// 1) api_keys
const e = crypto.encrypt(KEY);
const existingKey = db.prepare("SELECT id FROM api_keys WHERE platform='custom' AND base_url=?").get(BASE);
let keyId;
if (existingKey) {
  keyId = existingKey.id;
  console.log(`api_key exists id=${keyId}`);
} else {
  const r = db.prepare(
    "INSERT INTO api_keys (platform,label,encrypted_key,iv,auth_tag,status,enabled,base_url) VALUES ('custom',?,?,?,?,'unknown',1,?)"
  ).run('g4f-1337', e.encrypted, e.iv, e.authTag, BASE);
  keyId = r.lastInsertRowid;
  console.log(`api_key inserted id=${keyId}`);
}

// 2) models + 3) fallback_config
const MODELS = [
  // [model_id, display_name, intel_rank, speed_rank, size_label, rpm, rpd, ctx, vision, tools]
  ['openai-fast', 'g4f Pollinations openai-fast', 12, 8, 'Cloud', 60, 1000, 131072, 1, 1],
];

for (const [mid, disp, ir, sr, sz, rpm, rpd, ctx, vision, tools] of MODELS) {
  const existing = db.prepare("SELECT id FROM models WHERE platform='custom' AND model_id=?").get(mid);
  let modelDbId;
  if (existing) {
    modelDbId = existing.id;
    console.log(`model exists id=${modelDbId} ${mid}`);
  } else {
    const r = db.prepare(
      `INSERT INTO models (platform,model_id,display_name,intelligence_rank,speed_rank,size_label,rpm_limit,rpd_limit,monthly_token_budget,context_window,enabled,supports_vision,key_id,supports_tools,source)
       VALUES ('custom',?,?,?,?,?,?,?,'free',?,1,?,?,?,'user')`
    ).run(mid, disp, ir, sr, sz, rpm, rpd, ctx, vision, keyId, tools);
    modelDbId = r.lastInsertRowid;
    console.log(`model inserted id=${modelDbId} ${mid}`);
  }
  const fb = db.prepare("SELECT id FROM fallback_config WHERE model_db_id=?").get(modelDbId);
  if (!fb) {
    const maxPri = db.prepare("SELECT COALESCE(MAX(priority),0) m FROM fallback_config").get().m;
    db.prepare("INSERT INTO fallback_config (model_db_id,priority,enabled) VALUES (?,?,1)").run(modelDbId, maxPri + 1);
    console.log(`fallback added priority=${maxPri + 1}`);
  } else {
    console.log('fallback exists');
  }
}

// verify decrypt round-trip
const row = db.prepare("SELECT encrypted_key,iv,auth_tag FROM api_keys WHERE id=?").get(keyId);
console.log('decrypt round-trip:', crypto.decrypt(row.encrypted_key, row.iv, row.auth_tag) === KEY ? 'OK' : 'FAIL');
db.pragma('wal_checkpoint(TRUNCATE)');
console.log('DONE');
