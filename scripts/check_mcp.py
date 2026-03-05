#!/usr/bin/env python3
"""End-to-end MCP availability check for Horizon MCP."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_TOOLS = {
    "hz_validate_config",
    "hz_fetch_items",
    "hz_score_items",
    "hz_filter_items",
    "hz_enrich_items",
    "hz_generate_summary",
    "hz_run_pipeline",
    "hz_list_runs",
    "hz_get_run_meta",
    "hz_get_run_stage",
    "hz_get_run_summary",
    "hz_get_metrics",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Horizon MCP over stdio")
    parser.add_argument(
        "--horizon-path",
        default="/tmp/Horizon",
        help="Path to Horizon repository for validate call",
    )
    return parser.parse_args()


async def check_mcp(horizon_path: str) -> int:
    params = StdioServerParameters(
        command="python3",
        args=["-m", "horizon_mcp.server"],
        cwd=str(ROOT),
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tool_names = {tool.name for tool in tools_result.tools}
            missing_tools = sorted(REQUIRED_TOOLS - tool_names)
            if missing_tools:
                print("❌ 缺少工具:", ", ".join(missing_tools))
                return 1

            resources_result = await session.list_resources()
            resource_uris = [str(resource.uri) for resource in resources_result.resources]
            templates_result = await session.list_resource_templates()
            template_uris = [str(t.uriTemplate) for t in templates_result.resourceTemplates]

            validate_result = await session.call_tool(
                "hz_validate_config",
                {"horizon_path": horizon_path},
            )

            payload = validate_result.structuredContent
            if not isinstance(payload, dict):
                print("❌ hz_validate_config 返回结构异常")
                return 1

            print("✅ Horizon MCP 可用")
            print(f"tools: {len(tool_names)}")
            print(f"resources: {len(resource_uris)}")
            print(f"resource_templates: {len(template_uris)}")
            print("sample validate:")
            print(json.dumps(payload, ensure_ascii=False, indent=2)[:1000])
            return 0


def main() -> None:
    args = parse_args()
    code = asyncio.run(check_mcp(args.horizon_path))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
