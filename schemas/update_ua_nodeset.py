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
    p_v1 = Path("./UA-Nodeset")
    p_v1_backup = Path("./UA-Nodeset-backup")
    p_v2 = Path("./UA-Nodeset-master")
    p_v2_backup = Path("./UA-Nodeset-master-backup")
    if p_v1.is_dir():
        p_v1.rename(str(p_v2))
    elif p_v2.is_dir():
        p_v2.rename(str(p_v2_backup))
    try:
        check_call(["git", "clone", "--depth=1",
                    "https://github.com/OPCFoundation/UA-Nodeset.git", "UA-Nodeset-master"], timeout=timeout)
    except CalledProcessError:
        if p_v1_backup.is_dir():
            p_v1_backup.rename(str(p_v1))
        elif p_v2_backup.is_dir():
            p_v2_backup.rename(str(p_v2))
            logger.warning("Failed to clone repository. Try continue with old Nodeset folder.")
        else:
            raise UpdateError("Nodeset neither existed nor was downloaded. Abort update.")
    except TimeoutExpired:
        raise UpdateError(f"Timeout expired - Waited {timeout} seconds to clone from repo."
                          f" Either change value or check network connection. Abort update.")
    if p_v1_backup.is_dir():
        rm_tree(p_v1_backup)
    elif p_v2_backup.is_dir():
        rm_tree(p_v2_backup)
    rm_tree(Path("./UA-Nodeset-master/.git"))
    rm_tree(Path("./UA-Nodeset-master/.github"))
    Path("./UA-Nodeset-master/PublishNodeSets.bat").unlink()


def generate_standard_nodesets():
    run_module("generate_address_space")
    run_module("generate_event_objects")
    run_module("generate_ids")
    run_module("generate_model")
    run_module("generate_model_event")
    run_module("generate_protocol_python")
    run_module("generate_event_objects")
    run_module("generate_statuscode")
    run_module("generate_uaerrors")


if __name__ == "__main__":
    logger.debug("Try creating new Nodeset from github source")
    get_new_nodeset()
    generate_standard_nodesets()
    logger.debug("UA Nodeset created successfully")
