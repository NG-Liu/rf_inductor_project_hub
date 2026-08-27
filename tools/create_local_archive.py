from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable


DESKTOP = Path.home() / "Desktop"
ARCHIVE_DATE = date.today().isoformat()
ARCHIVE_NAME = f"RF_Inductor_Project_Archive_{ARCHIVE_DATE}"
EXCLUDED_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
}
EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo"}


def default_sources() -> list[tuple[str, Path, str]]:
    return [
        ("inductor_core", DESKTOP / "single_inductor_lq_surrogate", "01_single_inductor_lq_surrogate"),
        ("inductor_release", DESKTOP / "emx_inductor_optimizer_release", "02_emx_inductor_optimizer_release"),
        ("rf_integration_legacy", DESKTOP / "新建文件夹 (2)", "03_rf_integration_legacy"),
        ("project_hub", DESKTOP / "rf_inductor_project_hub", "04_rf_inductor_project_hub"),
    ]


def git_repositories(sources: list[tuple[str, Path, str]]) -> list[tuple[str, Path]]:
    legacy = next(path for source_id, path, _ in sources if source_id == "rf_integration_legacy")
    return [
        ("inductor_core", next(path for source_id, path, _ in sources if source_id == "inductor_core")),
        ("inductor_release", next(path for source_id, path, _ in sources if source_id == "inductor_release")),
        ("rf_integration_legacy", legacy),
        ("lvbobalun_development", legacy / "repo_lvbobalun"),
        ("lvbobalun_reference", legacy / "external" / "LVBOBALUN"),
        ("project_hub", next(path for source_id, path, _ in sources if source_id == "project_hub")),
    ]


def ignored_copy_items(directory: str, names: list[str]) -> set[str]:
    del directory
    return {
        name
        for name in names
        if name in EXCLUDED_DIR_NAMES or Path(name).suffix.lower() in EXCLUDED_FILE_SUFFIXES
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(path: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout


def write_git_snapshot(name: str, repository: Path, destination: Path) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=True)
    snapshot: dict[str, object] = {"name": name, "source": str(repository), "exists": repository.exists()}
    if not (repository / ".git").exists():
        snapshot["git_repository"] = False
        return snapshot

    snapshot["git_repository"] = True
    commands = {
        "status.txt": ("status", "--short"),
        "branches.txt": ("branch", "--all", "--verbose", "--no-abbrev"),
        "remotes.txt": ("remote", "-v"),
        "recent_log.txt": ("log", "--all", "--decorate", "--oneline", "-50"),
        "unstaged.diff": ("diff", "--binary"),
        "staged.diff": ("diff", "--cached", "--binary"),
    }
    for filename, command in commands.items():
        code, output = run_git(repository, *command)
        (destination / filename).write_text(output, encoding="utf-8")
        snapshot[filename] = {"exit_code": code, "bytes": len(output.encode("utf-8"))}

    bundle_path = destination / f"{name}.bundle"
    code, output = run_git(repository, "bundle", "create", str(bundle_path), "--all")
    (destination / "bundle.log").write_text(output, encoding="utf-8")
    snapshot["bundle_exit_code"] = code
    snapshot["bundle"] = bundle_path.name if bundle_path.exists() else ""
    return snapshot


def iter_files(root: Path) -> Iterable[Path]:
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIR_NAMES)
        for name in sorted(names):
            path = Path(directory) / name
            if path.suffix.lower() not in EXCLUDED_FILE_SUFFIXES:
                yield path


def write_source_readme(destination: Path, sources: list[tuple[str, Path, str]], git_snapshots: list[dict[str, object]]) -> None:
    lines = [
        "# RF Inductor Project Archive",
        "",
        f"Created: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Contents",
        "",
    ]
    for source_id, source, archive_directory in sources:
        lines.append(f"- `{archive_directory}/`: working-copy snapshot of `{source_id}` from `{source}`")
    lines.extend(
        [
            "- `05_git_history/`: Git bundles and status/diff snapshots for each repository.",
            "- `00_SOURCE_MANIFEST.csv`: SHA-256 inventory of every archived file.",
            "- `00_ARCHIVE_METADATA.json`: source paths, exclusions, and Git export results.",
            "",
            "## Deliberate Exclusions",
            "",
            "The copied working trees exclude `.git` directories and Python/editor caches. Git history is preserved separately as bundles and state snapshots under `05_git_history/`. All source files, generated layouts, solver results, reports, videos, images, and untracked materials outside those exclusions are copied.",
            "",
            "## Restoring Git History",
            "",
            "To inspect a repository bundle, create an empty Git repository and fetch from the corresponding `.bundle` file. The working-copy snapshot contains the exact file-state copy, including any uncommitted source changes present at archive time.",
        ]
    )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(archive_root: Path) -> tuple[int, int]:
    manifest_path = archive_root / "00_SOURCE_MANIFEST.csv"
    total_bytes = 0
    count = 0
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["archive_relative_path", "size_bytes", "sha256", "modified_at_utc"],
        )
        writer.writeheader()
        for file in sorted(iter_files(archive_root), key=lambda item: item.as_posix().lower()):
            if file == manifest_path:
                continue
            stat = file.stat()
            writer.writerow(
                {
                    "archive_relative_path": file.relative_to(archive_root).as_posix(),
                    "size_bytes": stat.st_size,
                    "sha256": sha256(file),
                    "modified_at_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                }
            )
            total_bytes += stat.st_size
            count += 1
    return count, total_bytes


def create_zip(archive_root: Path, zip_path: Path) -> tuple[int, int]:
    count = 0
    total_bytes = 0
    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as archive:
        for file in sorted(iter_files(archive_root), key=lambda item: item.as_posix().lower()):
            archive.write(file, archive_root.name / file.relative_to(archive_root))
            count += 1
            total_bytes += file.stat().st_size
    return count, total_bytes


def ensure_destination_is_safe(destination: Path, sources: list[tuple[str, Path, str]], resume: bool) -> None:
    resolved_destination = destination.resolve()
    if destination.exists() and not resume:
        raise FileExistsError(f"Archive destination already exists: {destination}")
    for _, source, _ in sources:
        resolved_source = source.resolve()
        if resolved_destination == resolved_source or resolved_source in resolved_destination.parents:
            raise ValueError(f"Archive destination must not be inside a source tree: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a non-destructive local RF inductor project archive and ZIP.")
    parser.add_argument("--destination", type=Path, default=DESKTOP / ARCHIVE_NAME)
    parser.add_argument("--zip", dest="zip_path", type=Path, default=DESKTOP / f"{ARCHIVE_NAME}.zip")
    parser.add_argument("--resume", action="store_true", help="Continue a partial archive at an existing destination.")
    parser.add_argument("--replace-zip", action="store_true", help="Replace an existing ZIP while refreshing a resumed archive.")
    args = parser.parse_args()

    sources = default_sources()
    missing = [str(path) for _, path, _ in sources if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing archive sources:\n" + "\n".join(missing))
    ensure_destination_is_safe(args.destination, sources, args.resume)
    if args.zip_path.exists() and not args.replace_zip:
        raise FileExistsError(f"ZIP destination already exists: {args.zip_path}")

    args.destination.mkdir(parents=True, exist_ok=args.resume)
    print(f"archive root: {args.destination}")
    for source_id, source, archive_directory in sources:
        destination = args.destination / archive_directory
        print(f"copy {source_id}: {source} -> {destination}")
        shutil.copytree(
            source,
            destination,
            ignore=ignored_copy_items,
            copy_function=shutil.copy2,
            dirs_exist_ok=args.resume,
        )

    git_root = args.destination / "05_git_history"
    git_snapshots = [
        write_git_snapshot(name, repository, git_root / name)
        for name, repository in git_repositories(sources)
    ]
    write_source_readme(args.destination / "00_ARCHIVE_README.md", sources, git_snapshots)
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {"id": source_id, "path": str(source), "archive_directory": archive_directory}
            for source_id, source, archive_directory in sources
        ],
        "excluded_directory_names": sorted(EXCLUDED_DIR_NAMES),
        "excluded_file_suffixes": sorted(EXCLUDED_FILE_SUFFIXES),
        "git_snapshots": git_snapshots,
    }
    (args.destination / "00_ARCHIVE_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest_count, manifest_bytes = write_manifest(args.destination)
    zip_count, zip_bytes = create_zip(args.destination, args.zip_path)
    zip_hash = sha256(args.zip_path)
    sidecar = args.zip_path.with_suffix(args.zip_path.suffix + ".sha256")
    sidecar.write_text(f"{zip_hash} *{args.zip_path.name}\n", encoding="ascii")
    print(f"manifest files={manifest_count} source_bytes={manifest_bytes}")
    print(f"zip files={zip_count} input_bytes={zip_bytes}")
    print(f"zip={args.zip_path}")
    print(f"zip_sha256={zip_hash}")
    print(f"zip_sha256_file={sidecar}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"archive failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
