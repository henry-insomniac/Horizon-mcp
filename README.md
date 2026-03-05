# Horizon MCP

面向 [Horizon](https://github.com/Thysrael/Horizon) 的 MCP Server。

该服务不重写 Horizon 逻辑，而是直接复用 Horizon 原生模块，按阶段暴露为 MCP 工具：

- `hz_validate_config`
- `hz_fetch_items`
- `hz_score_items`
- `hz_filter_items`
- `hz_enrich_items`
- `hz_generate_summary`
- `hz_run_pipeline`

## 1. 前置要求

1. Python 3.11+
2. 本地可访问 Horizon 仓库（默认自动发现以下位置）
- `$HORIZON_PATH`
- `./Horizon`
- `../Horizon`
- `/Users/Zhuanz/work-space/Horizon`
- `/tmp/Horizon`

3. Horizon 配置文件存在：`<horizon_path>/data/config.json`

## 2. 安装与启动

```bash
cd /Users/Zhuanz/work-space/Horizon-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .

# stdio 启动（给 MCP 客户端使用）
horizon-mcp
```

## 3. 运行产物

所有运行都会落盘到：

- `data/mcp-runs/<run_id>/meta.json`
- `data/mcp-runs/<run_id>/raw_items.json`
- `data/mcp-runs/<run_id>/scored_items.json`
- `data/mcp-runs/<run_id>/filtered_items.json`
- `data/mcp-runs/<run_id>/enriched_items.json`
- `data/mcp-runs/<run_id>/summary-<lang>.md`

## 4. 工具说明

### `hz_validate_config`

校验 Horizon 路径、配置结构和关键环境变量。

主要参数：
- `horizon_path`（可选）
- `config_path`（可选）
- `sources`（可选，例：`["rss", "hackernews"]`）
- `check_env`（默认 `true`）

### `hz_fetch_items`

抓取并做 URL 去重，产出 `raw` 阶段。

主要参数：
- `hours`（默认 `24`）
- `run_id`（可选，不传自动生成）
- `horizon_path` / `config_path` / `sources`

### `hz_score_items`

基于 AI 对输入阶段打分，产出 `scored` 阶段。

主要参数：
- `run_id`（必填）
- `source_stage`（默认 `raw`）

### `hz_filter_items`

按阈值过滤并做主题去重，产出 `filtered` 阶段。

主要参数：
- `run_id`（必填）
- `threshold`（可选，默认用 Horizon 配置）
- `source_stage`（默认 `scored`）
- `topic_dedup`（默认 `true`）

### `hz_enrich_items`

对高分内容做背景知识富化，产出 `enriched` 阶段。

主要参数：
- `run_id`（必填）
- `source_stage`（默认 `filtered`）

### `hz_generate_summary`

按语言生成 Markdown 摘要。

主要参数：
- `run_id`（必填）
- `language`（默认 `zh`）
- `source_stage`（可选，不传自动选 `enriched/filtered/scored/raw`）
- `save_to_horizon_data`（默认 `false`，`true` 时写回 Horizon 的 `data/summaries/`）

### `hz_run_pipeline`

一键执行完整流程。

主要参数：
- `hours`、`languages`、`threshold`
- `sources`（可选）
- `enrich`（默认 `true`）
- `topic_dedup`（默认 `true`）
- `save_to_horizon_data`（默认 `false`）

## 5. 设计原则

1. 默认无外部副作用：不自动写 Horizon docs、不自动发邮件。
2. 阶段可重入：可用同一 `run_id` 分步执行并复用中间产物。
3. 保持与 Horizon 主项目一致：抓取、分析、富化、摘要均复用 Horizon 原生实现。

## 6. Git 身份（当前仓库）

已按要求设置为仓库本地配置：

- `user.name=henry-insomniac`
- `user.email=lovedangdang@outlook.com`

