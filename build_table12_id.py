# -*- coding: utf-8 -*-
"""
Generates the Indonesian translated data for Table 12 (Table A1 - Q01 to Q60).
"""

import json

with open("doc_dump.json", "r", encoding="utf-8") as f:
    data = json.load(f)

t12_raw = data["tables"][12]["data"]

cluster_map = {
    "1. Single-Fact Academic": "1. Fakta Tunggal Akademik",
    "2. Numerical Aggregation": "2. Agregasi Numerik",
    "3. Cross-Entity Comparison": "3. Perbandingan Lintas Entitas",
    "4. Multi-Hop Relational": "4. Relasional Multi-Hop",
    "5. Ambiguous & Robustness": "5. Ambiguitas & Ketahanan (Robustness)",
    "6. Privacy & Out-of-Scope": "6. Privasi & Luar Cakupan (Out-of-Scope)"
}

policy_map = {
    "No": "Tidak",
    "Clarify": "Klarifikasi",
    "Yes (Refuse PII)": "Ya (Tolak PII)",
    "Yes (Suppress small cell n=2)": "Ya (Supresi sel kecil n=2)",
    "Yes (Refuse differencing)": "Ya (Tolak differencing)",
    "Yes (Refuse OOS)": "Ya (Tolak di luar cakupan / OOS)",
    "Yes (Sanitize Cypher injection)": "Ya (Sanitasi injeksi Cypher)",
    "Yes (Suppress sub-cell n=1)": "Ya (Supresi sub-sel n=1)"
}

rows_id = []
# Header
header = [
    "ID",
    "Klaster",
    "Prompt Pertanyaan (Bahasa Indonesia)",
    "Kebenaran Dasar Terverifikasi & Sumber Data",
    "Kebijakan Penolakan / Privasi",
    "Audit Router: Sebelum Perbaikan vs Setelah Perbaikan"
]
rows_id.append(header)

for row in t12_raw[1:]:
    qid = row[0]
    cluster_en = row[1]
    cluster_id = cluster_map.get(cluster_en, cluster_en)
    
    # Prompt: extract prompt
    prompt = row[2]
    # In row[2], the prompt has Indonesian question first, then [EN: ...]
    # We can keep prompt as is (or keep Indonesian question clean)
    # Keeping both or Indonesian clean: Let's keep Indonesian question + [EN: ...] so it retains bilingual trace
    prompt_id = prompt
    
    # Ground truth
    gt = row[3]
    gt_id = gt.replace("(Source:", "(Sumber:").replace("higher than", "lebih tinggi daripada").replace("lower than", "lebih rendah daripada")
    gt_id = gt_id.replace("Safe refusal:", "Penolakan aman:").replace("Ambiguous:", "Ambigu:")
    gt_id = gt_id.replace("tracked respondents", "responden terlacak").replace("graduates", "lulusan")
    gt_id = gt_id.replace("total semester 1", "total semester 1")
    
    # Policy
    policy = row[4]
    policy_id = policy_map.get(policy, policy)
    if "Yes (" in policy:
        policy_id = policy.replace("Yes (", "Ya (").replace("Refuse", "Tolak").replace("Suppress", "Supresi").replace("Sanitize", "Sanitasi")
    
    # Audit
    audit = row[5]
    audit_id = audit.replace("Before:", "Sebelum:").replace("After:", "Setelah:")
    audit_id = audit_id.replace("No $param binding", "Tanpa pengikatan $param")
    audit_id = audit_id.replace("Single-branch Cypher misses cross-domain multi-hop", "Cypher cabang tunggal melewatkan multi-hop lintas domain")
    audit_id = audit_id.replace("No privacy/refusal guard in router", "Tanpa penjaga privasi/penolakan pada router")
    audit_id = audit_id.replace("Typo/synonym unhandled", "Typo/sinonim tidak tertangani")
    audit_id = audit_id.replace("Collision on", "Tabrakan pada")
    audit_id = audit_id.replace("Missing year filter fallback", "Filter tahun hilang fallback")
    audit_id = audit_id.replace("Cypher injection vulnerability", "Kerentanan injeksi Cypher")
    
    rows_id.append([qid, cluster_id, prompt_id, gt_id, policy_id, audit_id])

print(f"Generated {len(rows_id)} rows for Table 12 (Table A1).")

with open("table_12_id.json", "w", encoding="utf-8") as f:
    json.dump(rows_id, f, ensure_ascii=False, indent=2)

print("Saved table_12_id.json")
