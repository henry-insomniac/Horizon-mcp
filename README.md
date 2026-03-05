# Horizon MCP

面向 [Horizon](https://github.com/Thysrael/Horizon) 的 MCP Server。

服务直接复用 Horizon 原生 Python 实现，按阶段暴露工具，不重复造业务逻辑。

## 1. 能力概览

### 工具（Tools）

- `hz_validate_config`
- `hz_fetch_items`
- `hz_score_items`
- `hz_filter_items`
- `hz_enrich_items`
- `hz_generate_summary`
- `hz_run_pipeline`
- `hz_list_runs`
- `hz_get_run_meta`
- `hz_get_run_stage`
- `hz_get_run_summary`
- `hz_get_metrics`

### 资源（Resources）

- `horizon://server/info`
- `horizon://metrics`
- `horizon://runs`
- `horizon://runs/{run_id}/meta`
- `horizon://runs/{run_id}/items/{stage}`
- `horizon://runs/{run_id}/summary/{language}`
- `horizon://config/effective`

## 2. 前置要求

1. Python 3.11+
2. 本地可访问 Horizon 仓库（自动发现顺序）
- `$HORIZON_PATH`
- `./Horizon`
- `../Horizon`
- `/Users/Zhuanz/work-space/Horizon`
- `/tmp/Horizon`

3. Horizon 配置文件存在：`<horizon_path>/data/config.json`

## 3. 安装与启动

```bash
cd /Users/Zhuanz/work-space/Horizon-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .

# stdio 启动（给 MCP 客户端使用）
horizon-mcp
```

## 4. 运行产物

每次 run 会写入：`data/mcp-runs/<run_id>/`

- `meta.json`
- `raw_items.json`
- `scored_items.json`
- `filtered_items.json`
- `enriched_items.json`
- `summary-<lang>.md`

## 5. 设计原则

1. 默认无外部副作用：不自动写 Horizon docs、不自动发邮件。
2. 阶段可重入：同一 `run_id` 可分步执行。
3. 保持主逻辑一致：抓取、评分、富化、总结全部复用 Horizon 原生模块。

## 6. 客户端接入

接入示例见：[docs/integration.md](docs/integration.md)

快速连通检查：

```bash
cd /Users/Zhuanz/work-space/Horizon-mcp
make check-mcp
```

## 7. Git 身份（当前仓库）

本仓库已设置：

- `user.name=henry-insomniac`
- `user.email=lovedangdang@outlook.com`
