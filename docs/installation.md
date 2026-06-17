# 安装说明

## 作为 git submodule 添加

```bash
git submodule add <repository-url> agent-system/oh-my-autoresearch
cd agent-system/oh-my-autoresearch
```

## 运行 install.sh

```bash
./install.sh <host-repo-root>
```

安装脚本将：
1. 复制 `.claude.template/` → `<host-repo-root>/.claude/`
2. 复制 `runtime.template/` → `<host-repo-root>/runtime/`
3. 不覆盖用户已有数据
4. 设置脚本执行权限
5. 自动调用 `bootstrap.sh`

## 初始化 objective

```bash
cp runtime/states/objective.example.json runtime/states/objective.json
# 编辑 objective.json 填入训练配置
```

## 首次运行 /loop

在 Claude Code 中执行 `/loop` 启动研究循环。
