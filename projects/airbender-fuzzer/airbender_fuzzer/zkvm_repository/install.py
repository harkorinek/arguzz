import logging
from pathlib import Path

from airbender_fuzzer.settings import (
    AIRBENDER_ZKVM_GIT_REPOSITORY,
)
from zkvm_fuzzer_utils.git import (
    git_clone_and_switch,
    git_reset_and_switch,
    is_git_repository,
)

logger = logging.getLogger("fuzzer")


def install_airbender(
    airbender_install_path: Path,
    commit_or_branch: str,
    *,
    enable_zkvm_modification: bool = False,
):
    logger.info(f"installing airbender zkvm @ {airbender_install_path}")

    # check if we already have the repository
    if not is_git_repository(airbender_install_path):
        # pull the repository from the official airbender github page
        logger.info(f"cloning airbender repo to {airbender_install_path}")
        git_clone_and_switch(airbender_install_path,
                             AIRBENDER_ZKVM_GIT_REPOSITORY, commit_or_branch)
    else:
        # reset all current changes and pull the newest version
        logger.info(
            f"resetting and pulling changes for airbender repo @ {airbender_install_path}")
        git_reset_and_switch(airbender_install_path, commit_or_branch)
