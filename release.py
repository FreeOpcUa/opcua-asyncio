import shutil
import subprocess
import sys
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
ALLOWED_BRANCHES = ("main", "master", "v2")
BUMP_KINDS = ("major", "minor", "patch")


def _run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def _confirm(prompt: str) -> bool:
    return input(prompt).strip().lower() in ("", "y", "yes")


def _current_branch() -> str:
    return _run("git", "branch", "--show-current")


def _working_tree_clean() -> bool:
    unstaged = subprocess.run(["git", "diff", "--quiet"], check=False).returncode
    staged = subprocess.run(["git", "diff", "--quiet", "--cached"], check=False).returncode
    return unstaged == 0 and staged == 0


def _local_up_to_date() -> bool:
    subprocess.run(["git", "fetch"], check=True)
    local = _run("git", "rev-parse", "HEAD")
    upstream = _run("git", "rev-parse", "@{u}")
    return local == upstream


def _tag_exists(tag: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"], check=False).returncode == 0


def _bump_version(bump: str) -> str:
    subprocess.run(["uv", "version", "--bump", bump], check=True)
    return _run("uv", "version", "--short")


def _restore_pyproject() -> None:
    subprocess.run(["git", "checkout", "--", str(PYPROJECT)], check=True)


def _publish() -> None:
    for directory in ("dist", "build"):
        shutil.rmtree(directory, ignore_errors=True)
    subprocess.run(["uv", "build"], check=True)
    subprocess.run(["uv", "publish"], check=True)


def release(bump: str) -> None:
    branch = _current_branch()
    if branch not in ALLOWED_BRANCHES:
        print(f"Not on main/master branch ({branch}), will not release")
        return
    if not _working_tree_clean():
        print("Working tree unclean, will not release")
        return
    if not _local_up_to_date():
        print("Local branch is not up-to-date with origin, will not release")
        return

    new_version = _bump_version(bump)
    tag = f"v{new_version}"
    if _tag_exists(tag):
        _restore_pyproject()
        print(f"Tag {tag} already exists, will not release")
        return

    if not _confirm(f"version bumped to {new_version}, commiting?(Y/n)"):
        _restore_pyproject()
        return

    subprocess.run(["git", "add", str(PYPROJECT)], check=True)
    subprocess.run(["git", "commit", "-m", f"new release: {new_version}"], check=True)
    subprocess.run(["git", "tag", "-a", tag, "-m", f"Release {new_version}"], check=True)

    if _confirm("change committed, push to server?(Y/n)"):
        subprocess.run(["git", "push", "--follow-tags"], check=True)

    if _confirm("upload to pip?(Y/n)"):
        _publish()


def main() -> None:
    if len(sys.argv) == 1:
        bump = "patch"
    else:
        if (bump := sys.argv[1]) not in BUMP_KINDS:
            raise ValueError(f"Argument needs to be one of {BUMP_KINDS}, not {bump}")
    release(bump)


if __name__ == "__main__":
    main()
