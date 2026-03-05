# Horizon MCP

面向 [Horizon](https://github.com/Thysrael/Horizon) 的 MCP Server。

服务直接复用 Horizon 原生 Python 实现，按阶段暴露工具，不重复造业务逻辑。

## 1. 能力概览

### 工具（Tools）

- `hz_validate_config`：校验 Horizon 配置有效性与关键环境变量是否齐全。
- `hz_fetch_items`：抓取并去重新闻内容，写入 `raw` 阶段。
- `hz_score_items`：调用 AI 对指定阶段内容打分，写入 `scored` 阶段。
- `hz_filter_items`：按分数阈值过滤并做主题去重，写入 `filtered` 阶段。
- `hz_enrich_items`：对高分内容执行背景富化，写入 `enriched` 阶段。
- `hz_generate_summary`：从指定阶段内容生成 Markdown 摘要。
- `hz_run_pipeline`：一键执行抓取、打分、过滤、富化、摘要全流程。
- `hz_list_runs`：列出最近 run 记录及各阶段产物状态。
- `hz_get_run_meta`：读取指定 run 的元数据。
- `hz_get_run_stage`：读取指定 run 的阶段内容（raw/scored/filtered/enriched）。
- `hz_get_run_summary`：读取指定 run 的摘要内容。
- `hz_get_metrics`：读取服务内存指标与调用统计。

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

4. （可选）MCP 密钥配置文件（避免手动 export）：
- `.cursor/mcp.secrets.json`
- `.cursor/mcp.secrets.local.json`
- `config/mcp.secrets.json`
- `config/mcp.secrets.local.json`
- `<horizon_path>/data/mcp.secrets.json`
- `<horizon_path>/data/mcp-secrets.json`

支持字段：

```json
{
  "OPENAI_API_KEY": "sk-xxxx",
  "GITHUB_TOKEN": "ghp_xxxx"
}
```

也支持嵌套写法：

```json
{
  "env": {
    "OPENAI_API_KEY": "sk-xxxx",
    "GITHUB_TOKEN": "ghp_xxxx"
  }
}
```

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
