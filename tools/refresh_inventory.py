from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HUB_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = HUB_ROOT / "projects.json"
INVENTORY_DIR = HUB_ROOT / "inventory"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
RESULT_FILENAMES = {
    "best_result.json",
    "proposal.json",
    "run_overnight_summary.json",
    "emx_batch_summary.json",
    "run.json",
    "score_summary.json",
    "manifest.csv",
    "summary.md",
}


def load_projects(config_path: Path) -> list[dict[str, str]]:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data["projects"]


def git_value(path: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def iter_files(path: Path):
    for root, dirs, names in os.walk(path):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in names:
            yield Path(root) / name


def group_kind(name: str) -> str:
    lowered = name.lower()
    if lowered in {"src", "scripts", "tests", "tools"}:
        return "source"
    if lowered in {"docs", "00_context"}:
        return "documentation"
    if lowered in {"data", "configs"}:
        return "data_or_config"
    if lowered in {"runs", "emx_cascade_results", "manual_emx_results"}:
        return "simulation_results"
    if lowered in {"tmp", "tmp_emx_scripts", "tmp_lefdef", "external"}:
        return "archive_or_reference"
    return "workspace_group"


def top_level_rows(project: dict[str, str]) -> list[dict[str, Any]]:
    root = Path(project["path"])
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows

    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if child.name in IGNORED_DIRS:
            continue
        if child.is_file():
            files = [child]
        elif child.is_dir():
            files = list(iter_files(child))
        else:
            continue
        extensions = Counter(file.suffix.lower() or "[no extension]" for file in files)
        total_bytes = sum(file.stat().st_size for file in files)
        rows.append(
            {
                "project_id": project["id"],
                "role": project["role"],
                "group": child.name,
                "kind": group_kind(child.name),
                "relative_path": child.relative_to(root).as_posix(),
                "file_count": len(files),
                "size_bytes": total_bytes,
                "top_extensions": "; ".join(
                    f"{suffix}:{count}" for suffix, count in extensions.most_common(5)
                ),
            }
        )
    return rows


def read_json(path: Path) -> Any | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value


def run_root(relative_path: Path) -> str:
    parts = relative_path.parts
    if "runs" not in parts:
        return relative_path.parent.as_posix()
    index = parts.index("runs")
    return Path(*parts[: index + 2]).as_posix() if len(parts) > index + 1 else "runs"


def result_row(project: dict[str, str], file: Path) -> dict[str, Any]:
    root = Path(project["path"])
    relative = file.relative_to(root)
    row: dict[str, Any] = {
        "project_id": project["id"],
        "run_root": run_root(relative),
        "record_type": file.name,
        "record_path": relative.as_posix(),
        "run_id": "",
        "domain": "",
        "parent_run_id": "",
        "source_commit": "",
        "tool": "",
        "process_id": "",
        "target_l_3p75_nh": "",
        "candidate_id": "",
        "l_3p75_nh": "",
        "q_3p75": "",
        "status": "",
        "size_bytes": file.stat().st_size,
        "modified_at": datetime.fromtimestamp(file.stat().st_mtime, timezone.utc).isoformat(),
    }
    if file.suffix.lower() != ".json":
        return row

    data = read_json(file)
    if data is None:
        row["status"] = "unreadable_json"
        return row
    if isinstance(data, list):
        row["status"] = "summary_list"
        if data and isinstance(data[0], dict):
            row["candidate_id"] = data[0].get("candidate_id", "")
        return row
    if not isinstance(data, dict):
        row["status"] = "unsupported_json"
        return row
    if file.name == "run.json":
        tool = data.get("tool")
        row["run_id"] = data.get("run_id", "")
        row["domain"] = data.get("domain", "")
        row["parent_run_id"] = data.get("parent_run_id", "")
        row["source_commit"] = data.get("source_commit", "")
        row["tool"] = tool.get("name", "") if isinstance(tool, dict) else str(tool or "")
        row["process_id"] = data.get("process_id", "")
        row["status"] = data.get("status", "")
        row["run_root"] = relative.parent.as_posix()
        return row
    best = data.get("best") if isinstance(data.get("best"), dict) else data
    row["target_l_3p75_nh"] = data.get("target_L_3p75_nH", data.get("target_L_nH", ""))
    row["candidate_id"] = best.get("candidate_id", "") if isinstance(best, dict) else ""
    row["l_3p75_nh"] = best.get("L_3p75_nH", "") if isinstance(best, dict) else ""
    row["q_3p75"] = best.get("Q_3p75", "") if isinstance(best, dict) else ""
    row["status"] = best.get("status", "") if isinstance(best, dict) else ""
    return row


def result_rows(project: dict[str, str]) -> list[dict[str, Any]]:
    root = Path(project["path"])
    if not root.exists():
        return []
    files = [
        file
        for file in iter_files(root)
        if file.name in RESULT_FILENAMES or file.name.endswith(".metrics.json")
    ]
    return [result_row(project, file) for file in sorted(files)]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the non-destructive RF project catalogs.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()

    projects = load_projects(args.config)
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
    project_rows: list[dict[str, Any]] = []
    run_rows: list[dict[str, Any]] = []
    summary_projects: list[dict[str, Any]] = []

    for project in projects:
        path = Path(project["path"])
        rows = top_level_rows(project)
        project_rows.extend(rows)
        run_rows.extend(result_rows(project))
        summary_projects.append(
            {
                **project,
                "exists": path.exists(),
                "git_head_current": git_value(path, "rev-parse", "HEAD"),
                "git_branch": git_value(path, "branch", "--show-current"),
                "git_status_entries": len(git_value(path, "status", "--porcelain=v1").splitlines()),
                "top_level_groups": len(rows),
            }
        )

    write_csv(
        INVENTORY_DIR / "project_inventory.csv",
        project_rows,
        ["project_id", "role", "group", "kind", "relative_path", "file_count", "size_bytes", "top_extensions"],
    )
    write_csv(
        INVENTORY_DIR / "run_catalog.csv",
        run_rows,
        [
            "project_id",
            "run_root",
            "record_type",
            "record_path",
            "run_id",
            "domain",
            "parent_run_id",
            "source_commit",
            "tool",
            "process_id",
            "target_l_3p75_nh",
            "candidate_id",
            "l_3p75_nh",
            "q_3p75",
            "status",
            "size_bytes",
            "modified_at",
        ],
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": summary_projects,
        "project_inventory_rows": len(project_rows),
        "run_catalog_rows": len(run_rows),
    }
    (INVENTORY_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {INVENTORY_DIR / 'project_inventory.csv'} ({len(project_rows)} rows)")
    print(f"wrote {INVENTORY_DIR / 'run_catalog.csv'} ({len(run_rows)} rows)")
    print(f"wrote {INVENTORY_DIR / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
