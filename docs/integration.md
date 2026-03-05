# MCP 客户端接入

## Cursor 示例

在仓库根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "horizon": {
      "command": "python3",
      "args": ["-m", "horizon_mcp.server"],
      "cwd": "/Users/Zhuanz/work-space/Horizon-mcp",
      "env": {
        "HORIZON_PATH": "/Users/Zhuanz/work-space/Horizon"
      }
    }
  }
}
```

修改后需要完全重启 Cursor。

## MCP 密钥配置文件

为避免在系统环境变量里手工配置，可在以下任一位置创建 JSON 文件：

- `.cursor/mcp.secrets.json`
- `.cursor/mcp.secrets.local.json`
- `config/mcp.secrets.json`
- `config/mcp.secrets.local.json`
- `<horizon_path>/data/mcp.secrets.json`
- `<horizon_path>/data/mcp-secrets.json`

支持以下两种格式：

```json
{
  "OPENAI_API_KEY": "sk-xxxx",
  "GITHUB_TOKEN": "ghp_xxxx"
}
```

```json
{
  "env": {
    "OPENAI_API_KEY": "sk-xxxx",
    "GITHUB_TOKEN": "ghp_xxxx"
  }
}
```

如需自定义路径，可在 MCP server `env` 中加：

```json
{
  "HORIZON_MCP_SECRETS_PATH": "/absolute/path/to/mcp.secrets.json"
}
```

## Codex Desktop 示例

将以下 server 配置加入你的 MCP 配置：

- command: `python3`
- args: `-m horizon_mcp.server`
- cwd: `/Users/Zhuanz/work-space/Horizon-mcp`
- env: `HORIZON_PATH=/Users/Zhuanz/work-space/Horizon`

## 连通检查

```bash
cd /Users/Zhuanz/work-space/Horizon-mcp
make check-mcp
```

该命令会：
1. 启动 MCP 服务（stdio）
2. 校验工具列表
3. 调用 `hz_validate_config` 做一次实测
