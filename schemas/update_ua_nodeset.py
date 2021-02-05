from shutil import rmtree
from os import unlink, path, rename
from subprocess import check_call, CalledProcessError, TimeoutExpired
from runpy import run_module

import logging
logger = logging.getLogger(__name__)


class UpdateError(Exception):
    pass


def get_new_nodeset():
    timeout = 120   # seconds
    if path.isdir("./UA-Nodeset"):
        rename("./UA-Nodeset", "./UA-Nodeset-old")
    elif path.isdir("./UA-Nodeset-master"):
        rename("./UA-Nodeset-master", "./UA-Nodeset-master-old")
    try:
        check_call(["git", "clone", "https://github.com/OPCFoundation/UA-Nodeset.git", "UA-Nodeset-master"], timeout=timeout)
    except CalledProcessError:
        if path.isdir("./UA-Nodeset"):
            rename("./UA-Nodeset-old", "./UA-Nodeset")
        elif path.isdir("./UA-Nodeset-master"):
            rename("./UA-Nodeset-master-old", "./UA-Nodeset-master")
            logger.warning("Failed to clone repository. Try continue with old Nodeset folder.")
        else:
            raise UpdateError("Nodeset neither existed nor was downloaded. Abort update.")
    except TimeoutExpired:
        raise UpdateError(f"Timeout expired - Waited {timeout} seconds to clone from repo."
                          f" Either change value or check network connection. Abort update.")
    if path.isdir("./UA-Nodeset-old"):
        rmtree("./UA-Nodeset-old")
    elif path.isdir("./UA-Nodeset-master-old"):
        rmtree("./UA-Nodeset-master-old")
    rmtree("./UA-Nodeset-master/.git")
    rmtree("./UA-Nodeset-master/.github")
    unlink("./UA-Nodeset-master/PublishNodeSets.bat")


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
