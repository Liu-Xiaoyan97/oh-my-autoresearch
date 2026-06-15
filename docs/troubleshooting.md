# Troubleshooting 故障排查

## Observer 未启动

**症状**: 事件无法被消费，DB/knowledge 不更新

**排查**:
```bash
# 检查 observer 进程
cat runtime/observer/run/observer.pid
ps aux | grep observer_daemon

# 手动启动
runtime/observer/scripts/lifecycle/start_observer.sh
```

## Events 积压

**症状**: events.jsonl 行数远大于 offset 值

**排查**:
```bash
wc -l runtime/observer/events/events.jsonl
cat runtime/observer/offsets/events.offset
```

**解决**: 检查 observer 日志，确认是否有解析错误导致卡住。查看 deadletter.jsonl 是否有失败事件。

## Schema 校验失败

**症状**: Phase 0 校验报错

**排查**:
```bash
python runtime/scripts/validate/validate_runtime.py
```

**常见原因**:
- objective.json 缺少必填字段
- states.json 格式不正确
- baseline.json 不完整

## SQLite 写入失败

**症状**: observer 写入 experiments/exploration 表失败

**排查**:
```bash
# 检查数据库是否可写
sqlite3 runtime/db/runtime.sqlite "SELECT count(*) FROM experiments;"

# 检查权限
ls -la runtime/db/
```

**解决**: 确保 observer 进程对 db 目录有写权限。

## Baseline 不完整

**症状**: Phase 0 校验 baseline 失败

**排查**:
```bash
python runtime/scripts/validate/validate_baseline.py
```

**解决**: 确保 baseline.json 包含完整的评估字段（primary_metrics、command、devices 等）。

## Git Dirty

**症状**: Phase 0 校验 git clean 失败

**解决**:
```bash
# 查看未提交变动
git status

# 提交或暂存变动后重试
```

## SSH Chain 失败

**症状**: remote 训练配置校验失败

**排查**:
```bash
python runtime/scripts/utils/ssh_chain.py hosts.txt
```

**解决**: 检查 SSH 密钥配置、hosts 文件格式、网络连通性。

## Training Log 无法解析

**症状**: `monitor_training.py` 或 `parse_train_log.py` 报错

**排查**:
```bash
cat runtime/logs/train-of-<exp_name>.log | tail -50
```

**常见原因**:
- 训练框架输出格式变化
- 日志文件损坏或未完全写入
- 训练进程异常退出，日志不完整
