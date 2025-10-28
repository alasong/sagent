import json
import shutil
from pathlib import Path
from datetime import datetime


def copy_file(src: Path, dst_root: Path):
    rel = src.relative_to(ROOT)
    dest = dst_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_dir(src: Path, dst_root: Path, include_exts=None, include_files=None):
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(src)
        # Filter by extensions or explicit file names if provided
        if include_exts and p.suffix and p.suffix.lower() not in include_exts:
            continue
        if include_files and p.name not in include_files:
            continue
        dest = dst_root / src.relative_to(ROOT) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)


def build_manifest(root_dir: Path):
    files = [str(p.relative_to(root_dir)) for p in sorted(root_dir.rglob("*")) if p.is_file()]
    manifest_txt = root_dir / "MANIFEST.txt"
    manifest_json = root_dir / "manifest.json"
    manifest_txt.write_text("\n".join(files), encoding="utf-8")
    manifest_json.write_text(json.dumps({"files": files, "count": len(files)}, ensure_ascii=False, indent=2), encoding="utf-8")


def make_zip(build_dir: Path, dist_dir: Path, release_name: str) -> Path:
    zip_base = dist_dir / release_name
    # shutil.make_archive expects str paths
    created = shutil.make_archive(str(zip_base), 'zip', root_dir=str(dist_dir), base_dir=str(build_dir.name))
    # Avoid Path.with_suffix on names like agent-v1.0.0 which would trim the last .0
    return Path(created)


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
DOCS_DIR = ROOT / "docs"
CONFIG_DIR = ROOT / "config"
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = ROOT / "tests"
DIST_DIR = ROOT / "dist"


def main():
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    release_name = f"agent-v{version}"
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    build_dir = DIST_DIR / release_name
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Copy top-level files
    for top in [VERSION_FILE, CHANGELOG_FILE, ROOT / "requirements.txt"]:
        copy_file(top, build_dir)

    # Copy docs (include key external docs and the versioned release notes)
    doc_files = [
        DOCS_DIR / "feature_list.md",
        DOCS_DIR / "dev_guide.md",
        DOCS_DIR / "progress.md",
        DOCS_DIR / f"release_notes_v{version}.md",
    ]
    for df in doc_files:
        if df.exists():
            copy_file(df, build_dir)

    # Copy config directory entirely
    copy_dir(CONFIG_DIR, build_dir)

    # Copy selected scripts necessary for consumers
    include_script_names = {
        "__init__.py",
        "config_loader.py",
        "poc_local_validate.py",
        "generate_progress.py",
        "routing_explain.py",
        "timeline_view.py",
        "validate_config.py",
    }
    copy_dir(SCRIPTS_DIR, build_dir, include_files=include_script_names)

    # Include tests for verification (optional but helpful)
    copy_dir(TESTS_DIR, build_dir)

    # Build manifest files
    build_manifest(build_dir)

    # Add a simple release README
    readme = build_dir / "README_RELEASE.md"
    readme.write_text(
        (
            f"Release: {release_name}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            "Contents:\n"
            "- VERSION, CHANGELOG.md, requirements.txt\n"
            "- docs/: release notes, feature list, dev guide, progress\n"
            "- config/: routing, guardrails, output schema, prompts, models\n"
            "- scripts/: config loader, validation, progress, timeline, routing explain\n"
            "- tests/: unit tests for routing, schema, policies, retry, degrade, timeline\n\n"
            "Usage:\n"
            "1) pip install -r requirements.txt\n"
            "2) pytest -q\n"
            "3) python scripts/generate_progress.py\n"
        ),
        encoding="utf-8",
    )

    # Create zip archive
    zip_path = make_zip(build_dir, DIST_DIR, release_name)
    print(f"Built release: {zip_path}")
    print(f"Manifest: {build_dir / 'MANIFEST.txt'}")


if __name__ == "__main__":
    main()

