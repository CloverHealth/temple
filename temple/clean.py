"""
Functions for cleaning up temporary resources used by temple
"""
import subprocess

import temple.check
import temple.constants
import temple.utils


def _get_current_branch():
    """Determine the current git branch"""
    result = temple.utils.shell('git rev-parse --abbrev-ref HEAD', stdout=subprocess.PIPE)
    return result.stdout.decode('utf8').strip()


def clean():
    """Cleans up temporary resources

    Tries to clean up:

    1. The temporary update branch used during ``temple update``
    2. The primary update branch used during ``temple update``
    """
    temple.check.in_git_repo()

    current_branch = _get_current_branch()
    update_branch = temple.constants.UPDATE_BRANCH_NAME
    temp_update_branch = temple.constants.TEMP_UPDATE_BRANCH_NAME

    if current_branch in (update_branch, temp_update_branch):
        err_msg = (
            'You must change from the "{}" branch since it will be deleted during cleanup'
        ).format(current_branch)
        raise temple.exceptions.InvalidCurrentBranchError(err_msg)

    if temple.check._has_branch(update_branch):
        temple.utils.shell('git branch -D {}'.format(update_branch))
    if temple.check._has_branch(temp_update_branch):
        temple.utils.shell('git branch -D {}'.format(temp_update_branch))
