from subprocess import check_call, CalledProcessError, TimeoutExpired
from runpy import run_module
from pathlib import Path

import logging
logger = logging.getLogger(__name__)


class UpdateError(Exception):
    pass


def rm_tree(path: Path):
    for child in path.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    path.rmdir()


def get_new_nodeset(timeout=120):
    cwd = Path(".")
    target_v1 = cwd / "UA-Nodeset"
    backup_v1 = target_v1.parent / (target_v1.name + "_backup")
    target_v2 = cwd / "UA-Nodeset-master"
    backup_v2 = target_v2.parent / (target_v2.name + "_backup")
    if target_v1.is_dir():
        target_v1.rename(str(target_v2))
    elif target_v2.is_dir():
        target_v2.rename(str(backup_v2))
    try:
        check_call(["git", "clone", "--depth=1",
                    "https://github.com/OPCFoundation/UA-Nodeset.git", "UA-Nodeset-master"], timeout=timeout)
    except CalledProcessError:
        if backup_v1.is_dir():
            backup_v1.rename(str(target_v1))
        elif backup_v2.is_dir():
            backup_v2.rename(str(target_v2))
            logger.warning("Failed to clone repository. Try continue with old Nodeset folder.")
        else:
            raise UpdateError("Nodeset neither existed nor was downloaded. Abort update.")
    except TimeoutExpired:
        raise UpdateError(f"Timeout expired - Waited {timeout} seconds to clone from repo."
                          f" Either change value or check network connection. Abort update.")
    if backup_v1.is_dir():
        rm_tree(backup_v1)
    elif backup_v2.is_dir():
        rm_tree(backup_v2)
    rm_tree(target_v2 / ".git")
    rm_tree(target_v2 / ".github")
    (target_v2 / "PublishNodeSets.bat").unlink()


def generate_standard_nodesets():
    run_module("generate_address_space")
    run_module("generate_event_objects")
    run_module("generate_ids")
    run_module("generate_protocol_python")
    run_module("generate_model_event")
    run_module("generate_event_objects")
    run_module("generate_statuscode")
    run_module("generate_uaerrors")


if __name__ == "__main__":
    logger.debug("Try creating new Nodeset from github source")
    get_new_nodeset()
    generate_standard_nodesets()
    logger.debug("UA Nodeset created successfully")
