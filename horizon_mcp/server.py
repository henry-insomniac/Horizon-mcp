"""MCP server entrypoint for Horizon."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import HorizonMcpError
from .service import HorizonPipelineService


mcp = FastMCP(name="horizon-mcp")
service = HorizonPipelineService()


def _ok(tool: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": tool,
        "data": data,
    }


def _err(tool: str, error: Exception) -> dict[str, Any]:
    if isinstance(error, HorizonMcpError):
        code = error.code
        message = error.message
        details = error.details
    else:
        code = "HZ_INTERNAL_ERROR"
        message = str(error)
        details = None

    return {
        "ok": False,
        "tool": tool,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


@mcp.tool()
async def hz_validate_config(
    horizon_path: str | None = None,
    config_path: str | None = None,
    sources: list[str] | None = None,
    check_env: bool = True,
) -> dict[str, Any]:
    """校验 Horizon 配置和关键环境变量。"""

    tool = "hz_validate_config"
    try:
        data = await service.validate_config(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
            check_env=check_env,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_fetch_items(
    hours: int = 24,
    run_id: str | None = None,
    horizon_path: str | None = None,
    config_path: str | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """抓取并去重内容，写入 run 的 raw 阶段。"""

    tool = "hz_fetch_items"
    try:
        data = await service.fetch_items(
            hours=hours,
            run_id=run_id,
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_score_items(
    run_id: str,
    source_stage: str = "raw",
    horizon_path: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """对指定阶段内容执行 AI 打分，写入 scored 阶段。"""

    tool = "hz_score_items"
    try:
        data = await service.score_items(
            run_id=run_id,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_filter_items(
    run_id: str,
    threshold: float | None = None,
    source_stage: str = "scored",
    topic_dedup: bool = True,
    horizon_path: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """按阈值过滤并做主题去重，写入 filtered 阶段。"""

    tool = "hz_filter_items"
    try:
        data = await service.filter_items(
            run_id=run_id,
            threshold=threshold,
            source_stage=source_stage,
            topic_dedup=topic_dedup,
            horizon_path=horizon_path,
            config_path=config_path,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_enrich_items(
    run_id: str,
    source_stage: str = "filtered",
    horizon_path: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """对高分内容执行背景富化，写入 enriched 阶段。"""

    tool = "hz_enrich_items"
    try:
        data = await service.enrich_items(
            run_id=run_id,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_generate_summary(
    run_id: str,
    language: str = "zh",
    source_stage: str | None = None,
    horizon_path: str | None = None,
    config_path: str | None = None,
    save_to_horizon_data: bool = False,
) -> dict[str, Any]:
    """从某阶段内容生成 Markdown 摘要。"""

    tool = "hz_generate_summary"
    try:
        data = await service.generate_summary(
            run_id=run_id,
            language=language,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
            save_to_horizon_data=save_to_horizon_data,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


@mcp.tool()
async def hz_run_pipeline(
    hours: int = 24,
    languages: list[str] | None = None,
    threshold: float | None = None,
    horizon_path: str | None = None,
    config_path: str | None = None,
    sources: list[str] | None = None,
    enrich: bool = True,
    topic_dedup: bool = True,
    save_to_horizon_data: bool = False,
) -> dict[str, Any]:
    """一键执行抓取->打分->过滤->富化->摘要。"""

    tool = "hz_run_pipeline"
    try:
        data = await service.run_pipeline(
            hours=hours,
            languages=languages,
            threshold=threshold,
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
            enrich=enrich,
            topic_dedup=topic_dedup,
            save_to_horizon_data=save_to_horizon_data,
        )
        return _ok(tool, data)
    except Exception as exc:
        return _err(tool, exc)


def main() -> None:
    """Run MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
