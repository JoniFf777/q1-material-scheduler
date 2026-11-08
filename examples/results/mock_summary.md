# mock 场景结果

固定脚本离线验证，不能证明真实模型决策能力或稳定性。

| 场景 | 第几次 | 通过 | 失败原因 | 步数 | 工具次数 | tokens |
|---|---|---|---|---|---|---|
| S01_normal | 1 | PASS | — | 5 | 5 | 0 |
| S02_missing_info | 1 | PASS | — | 7 | 9 | 0 |
| S03_rule_risk | 1 | PASS | — | 7 | 13 | 0 |
| S04_slot_conflict | 1 | PASS | — | 6 | 6 | 0 |
| S05_hard_conflict | 1 | PASS | — | 6 | 6 | 0 |
| S06_duplicate | 1 | PASS | — | 6 | 6 | 0 |
| S06b_slot_changed | 1 | PASS | — | 5 | 5 | 0 |
| S07_save_failure | 1 | PASS | — | 6 | 6 | 0 |
| S08_tool_retry | 1 | PASS | — | 6 | 6 | 0 |
| S09_step_limit | 1 | PASS | — | 4 | 4 | 0 |
| S10_confirm_round2 | 1 | PASS | — | 6 | 6 | 0 |
