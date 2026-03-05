from __future__ import annotations

from pathlib import Path

import pytest

from horizon_mcp.run_store import RunStore


def test_create_run_writes_meta(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    run_id = store.create_run()
    meta = store.load_meta(run_id)

    assert run_id.startswith("run-")
    assert meta["run_id"] == run_id
    assert "created_at" in meta


def test_save_and_load_stage_items(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-fixed")
    items = [{"title": "foo"}, {"title": "bar"}]

    path = store.save_items(run_id, "raw", items)
    loaded = store.load_items(run_id, "raw")

    assert path.name == "raw_items.json"
    assert loaded == items
    assert store.has_stage(run_id, "raw") is True


def test_update_meta_sets_updated_at(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-meta")

    meta = store.update_meta(run_id, {"status": "done"})

    assert meta["status"] == "done"
    assert "updated_at" in meta


def test_save_and_load_summary(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-summary")

    saved = store.save_summary(run_id, "zh", "# 摘要")
    content = store.load_summary(run_id, "zh")

    assert saved.name == "summary-zh.md"
    assert content == "# 摘要"


def test_unsupported_stage_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-invalid-stage")

    with pytest.raises(ValueError, match="Unsupported stage"):
        store.save_items(run_id, "unknown", [])


def test_missing_run_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    with pytest.raises(FileNotFoundError, match="Run not found"):
        store.run_dir("missing-run")


def test_missing_artifact_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-missing-file")

    with pytest.raises(FileNotFoundError, match="Artifact not found"):
        store.read_json(run_id, "does-not-exist.json")
