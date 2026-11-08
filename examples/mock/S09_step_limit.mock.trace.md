# 运行 Trace

模式：mock；模型：scripted-mock；状态：incomplete

离线固定脚本，只验证流程；不证明真实模型决策效果。

| 步骤 | 动作 | 参数 | 返回摘要 | 后续动作 | 决策依据 |
|---|---|---|---|---|---|
| 1 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M01"} | 读取 M01（basic） | get_material {"material_id": "M02"} | 离线脚本验证此步骤 |
| 2 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M02"} | 读取 M02（basic） | get_material {"material_id": "M04"} | 离线脚本验证此步骤 |
| 3 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M04"} | 读取 M04（basic） | get_material {"material_id": "M07"} | 离线脚本验证此步骤 |
| 4 | get_material | {"reason": "离线脚本验证此步骤", "material_id": "M07"} | 读取 M07（basic） | 结束：incomplete | 离线脚本验证此步骤 |

Token 用量：{"prompt_tokens": 0, "completion_tokens": 0}
