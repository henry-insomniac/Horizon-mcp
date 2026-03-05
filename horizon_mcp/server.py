"""MCP server entrypoint for Horizon."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Awaitable, Callable

from mcp.server.fastmcp import FastMCP

from .errors import HorizonMcpError
from .service import HorizonPipelineService


mcp = FastMCP(name="horizon-mcp")
service = HorizonPipelineService()

SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
METRICS: dict[str, Any] = {
    "started_at": SERVER_STARTED_AT,
    "tool_calls_total": 0,
    "tool_calls_success": 0,
    "tool_calls_failed": 0,
    "tool_calls_by_name": {},
    "tool_errors_by_code": {},
    "tool_last_duration_ms": {},
    "last_error": None,
}


def _ok(tool: str, data: dict[str, Any], duration_ms: float | None = None) -> dict[str, Any]:
    payload = {
        "ok": True,
        "tool": tool,
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    if duration_ms is not None:
        payload["meta"]["duration_ms"] = round(duration_ms, 2)
    return payload


def _err(tool: str, error: Exception, duration_ms: float | None = None) -> dict[str, Any]:
    if isinstance(error, HorizonMcpError):
        code = error.code
        message = error.message
        details = error.details
    else:
        code = "HZ_INTERNAL_ERROR"
        message = str(error)
        details = None

    payload = {
        "ok": False,
        "tool": tool,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    if duration_ms is not None:
        payload["meta"]["duration_ms"] = round(duration_ms, 2)
    return payload


def _record_metrics(tool: str, ok: bool, duration_ms: float, error_code: str | None = None) -> None:
    METRICS["tool_calls_total"] += 1
    if ok:
        METRICS["tool_calls_success"] += 1
    else:
        METRICS["tool_calls_failed"] += 1

    by_name = METRICS["tool_calls_by_name"]
    by_name[tool] = by_name.get(tool, 0) + 1

    METRICS["tool_last_duration_ms"][tool] = round(duration_ms, 2)

    if error_code:
        by_code = METRICS["tool_errors_by_code"]
        by_code[error_code] = by_code.get(error_code, 0) + 1
        METRICS["last_error"] = {
            "tool": tool,
            "code": error_code,
            "at": datetime.now(timezone.utc).isoformat(),
        }


async def _run_tool(tool: str, runner: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
    started = perf_counter()
    try:
        data = await runner()
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics(tool, ok=True, duration_ms=elapsed_ms)
        return _ok(tool, data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err(tool, exc, duration_ms=elapsed_ms)
        code = payload["error"]["code"]
        _record_metrics(tool, ok=False, duration_ms=elapsed_ms, error_code=code)
        return payload


def _resource_result(resource: str, loader: Callable[[], Any]) -> dict[str, Any]:
    try:
        data = loader()
        return {
            "ok": True,
            "resource": resource,
            "data": data,
        }
    except Exception as exc:
        return _err(resource, exc)


def _metrics_snapshot() -> dict[str, Any]:
    uptime_seconds = (
        datetime.now(timezone.utc) - datetime.fromisoformat(METRICS["started_at"])
    ).total_seconds()
    return {
        **METRICS,
        "uptime_seconds": round(uptime_seconds, 2),
    }


@mcp.tool()
async def hz_validate_config(
    horizon_path: str | None = None,
    config_path: str | None = None,
    sources: list[str] | None = None,
    check_env: bool = True,
) -> dict[str, Any]:
    """校验 Horizon 配置和关键环境变量。"""

    return await _run_tool(
        "hz_validate_config",
        lambda: service.validate_config(
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
            check_env=check_env,
        ),
    )


@mcp.tool()
async def hz_fetch_items(
    hours: int = 24,
    run_id: str | None = None,
    horizon_path: str | None = None,
    config_path: str | None = None,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    """抓取并去重内容，写入 run 的 raw 阶段。"""

    return await _run_tool(
        "hz_fetch_items",
        lambda: service.fetch_items(
            hours=hours,
            run_id=run_id,
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
        ),
    )


@mcp.tool()
async def hz_score_items(
    run_id: str,
    source_stage: str = "raw",
    horizon_path: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """对指定阶段内容执行 AI 打分，写入 scored 阶段。"""

    return await _run_tool(
        "hz_score_items",
        lambda: service.score_items(
            run_id=run_id,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        ),
    )


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

    return await _run_tool(
        "hz_filter_items",
        lambda: service.filter_items(
            run_id=run_id,
            threshold=threshold,
            source_stage=source_stage,
            topic_dedup=topic_dedup,
            horizon_path=horizon_path,
            config_path=config_path,
        ),
    )


@mcp.tool()
async def hz_enrich_items(
    run_id: str,
    source_stage: str = "filtered",
    horizon_path: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    """对高分内容执行背景富化，写入 enriched 阶段。"""

    return await _run_tool(
        "hz_enrich_items",
        lambda: service.enrich_items(
            run_id=run_id,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
        ),
    )


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

    return await _run_tool(
        "hz_generate_summary",
        lambda: service.generate_summary(
            run_id=run_id,
            language=language,
            source_stage=source_stage,
            horizon_path=horizon_path,
            config_path=config_path,
            save_to_horizon_data=save_to_horizon_data,
        ),
    )


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

    return await _run_tool(
        "hz_run_pipeline",
        lambda: service.run_pipeline(
            hours=hours,
            languages=languages,
            threshold=threshold,
            horizon_path=horizon_path,
            config_path=config_path,
            sources=sources,
            enrich=enrich,
            topic_dedup=topic_dedup,
            save_to_horizon_data=save_to_horizon_data,
        ),
    )


@mcp.tool()
def hz_list_runs(limit: int = 20) -> dict[str, Any]:
    """列出最近运行记录与阶段状态。"""

    started = perf_counter()
    try:
        data = service.list_runs(limit=limit)
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics("hz_list_runs", ok=True, duration_ms=elapsed_ms)
        return _ok("hz_list_runs", data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err("hz_list_runs", exc, duration_ms=elapsed_ms)
        _record_metrics(
            "hz_list_runs",
            ok=False,
            duration_ms=elapsed_ms,
            error_code=payload["error"]["code"],
        )
        return payload


@mcp.tool()
def hz_get_run_meta(run_id: str) -> dict[str, Any]:
    """读取指定 run 的元数据。"""

    started = perf_counter()
    try:
        data = service.get_run_meta(run_id)
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics("hz_get_run_meta", ok=True, duration_ms=elapsed_ms)
        return _ok("hz_get_run_meta", data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err("hz_get_run_meta", exc, duration_ms=elapsed_ms)
        _record_metrics(
            "hz_get_run_meta",
            ok=False,
            duration_ms=elapsed_ms,
            error_code=payload["error"]["code"],
        )
        return payload


@mcp.tool()
def hz_get_run_stage(run_id: str, stage: str, max_items: int = 200) -> dict[str, Any]:
    """读取指定 run 的某一阶段内容。"""

    started = perf_counter()
    try:
        data = service.get_run_stage(run_id=run_id, stage=stage, max_items=max_items)
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics("hz_get_run_stage", ok=True, duration_ms=elapsed_ms)
        return _ok("hz_get_run_stage", data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err("hz_get_run_stage", exc, duration_ms=elapsed_ms)
        _record_metrics(
            "hz_get_run_stage",
            ok=False,
            duration_ms=elapsed_ms,
            error_code=payload["error"]["code"],
        )
        return payload


@mcp.tool()
def hz_get_run_summary(run_id: str, language: str = "zh") -> dict[str, Any]:
    """读取指定 run 的摘要内容。"""

    started = perf_counter()
    try:
        data = service.get_run_summary(run_id=run_id, language=language)
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics("hz_get_run_summary", ok=True, duration_ms=elapsed_ms)
        return _ok("hz_get_run_summary", data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err("hz_get_run_summary", exc, duration_ms=elapsed_ms)
        _record_metrics(
            "hz_get_run_summary",
            ok=False,
            duration_ms=elapsed_ms,
            error_code=payload["error"]["code"],
        )
        return payload


@mcp.tool()
def hz_get_metrics() -> dict[str, Any]:
    """读取服务内存指标。"""

    started = perf_counter()
    try:
        data = _metrics_snapshot()
        elapsed_ms = (perf_counter() - started) * 1000
        _record_metrics("hz_get_metrics", ok=True, duration_ms=elapsed_ms)
        return _ok("hz_get_metrics", data, duration_ms=elapsed_ms)
    except Exception as exc:
        elapsed_ms = (perf_counter() - started) * 1000
        payload = _err("hz_get_metrics", exc, duration_ms=elapsed_ms)
        _record_metrics(
            "hz_get_metrics",
            ok=False,
            duration_ms=elapsed_ms,
            error_code=payload["error"]["code"],
        )
        return payload


@mcp.resource("horizon://server/info")
def r_server_info() -> dict[str, Any]:
    """Server metadata resource."""

    return {
        "name": "horizon-mcp",
        "started_at": SERVER_STARTED_AT,
        "runs_root": str(service.run_store.root.resolve()),
    }


@mcp.resource("horizon://metrics")
def r_metrics() -> dict[str, Any]:
    """In-memory metrics snapshot."""

    return _resource_result("horizon://metrics", _metrics_snapshot)


@mcp.resource("horizon://runs")
def r_runs() -> dict[str, Any]:
    """Recent run list."""

    return _resource_result("horizon://runs", lambda: service.list_runs(limit=30))


@mcp.resource("horizon://runs/{run_id}/meta")
def r_run_meta(run_id: str) -> dict[str, Any]:
    """Run meta by run_id."""

    return _resource_result(
        f"horizon://runs/{run_id}/meta",
        lambda: service.get_run_meta(run_id),
    )


@mcp.resource("horizon://runs/{run_id}/items/{stage}")
def r_run_items(run_id: str, stage: str) -> dict[str, Any]:
    """Run staged items by run_id/stage."""

    return _resource_result(
        f"horizon://runs/{run_id}/items/{stage}",
        lambda: service.get_run_stage(run_id=run_id, stage=stage, max_items=200),
    )


@mcp.resource("horizon://runs/{run_id}/summary/{language}")
def r_run_summary(run_id: str, language: str) -> dict[str, Any]:
    """Run summary markdown by language."""

    return _resource_result(
        f"horizon://runs/{run_id}/summary/{language}",
        lambda: service.get_run_summary(run_id=run_id, language=language),
    )


@mcp.resource("horizon://config/effective")
def r_effective_config() -> dict[str, Any]:
    """Effective default config resolved from local Horizon path."""

    return _resource_result("horizon://config/effective", service.get_effective_config)


def main() -> None:
    """Run MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
