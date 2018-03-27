"""Utilities for performing checks and throwing useful error messages"""
import os
import subprocess

import temple.constants
import temple.exceptions
import temple.utils


def is_git_ssh_path(template_path):
    """Raises a `InvalidTemplatePathError` if ``template_path`` is not a git SSH url

    Note that the git SSH url must be in the form as provided from Github or from
    ``temple ls``. For example, ``git@github.com:user/template.git``.
    """
    if not template_path.startswith('git@github.com:') or not template_path.endswith('.git'):
        raise temple.exceptions.InvalidTemplatePathError(
            'The template path must be a git SSH url (e.g. "git@github.com:user/template.git")')


def _in_git_repo():
    """Returns True if inside a git repo, False otherwise"""
    ret = temple.utils.shell('git rev-parse', stderr=subprocess.DEVNULL, check=False)
    return ret.returncode == 0


def in_git_repo():
    """Raises `NotInGitRepoError` if not inside a git repository"""
    if not _in_git_repo():
        msg = 'Must be inside git repository of project to run this command.'
        raise temple.exceptions.NotInGitRepoError(msg)


def not_in_git_repo():
    """Raises `InGitRepoError` if inside of a git repository"""
    if _in_git_repo():
        msg = 'Cannot run inside of a git repository. Change to another directory.'
        raise temple.exceptions.InGitRepoError(msg)


def _in_clean_repo():
    """Returns True if the git repo is not dirty, False otherwise"""
    ret = temple.utils.shell('git diff-index --quiet HEAD --', check=False)
    return ret.returncode == 0


def in_clean_repo():
    """Raises `InDirtyRepoError` if inside a dirty repository"""
    if not _in_clean_repo():
        msg = 'Cannot run inside of a dirty git repository. Stash or commit changes.'
        raise temple.exceptions.InDirtyRepoError(msg)


def _has_branch(branch):
    """Return True if the target branch exists."""
    ret = temple.utils.shell('git rev-parse --verify {}'.format(branch),
                             stderr=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL,
                             check=False)
    return ret.returncode == 0


def not_has_branch(branch):
    """Raises `ExistingBranchError` if the specified branch exists."""
    if _has_branch(branch):
        msg = 'Cannot proceed while {} branch exists; remove and try again.'.format(branch)
        raise temple.exceptions.ExistingBranchError(msg)


def has_env_vars(*env_vars):
    """Raises `InvalidEnvironmentError` when one isnt set"""
    for env_var in env_vars:
        if not os.environ.get(env_var):
            msg = (
                'Must set {} environment variable. View docs for setting up environment at {}'
            ).format(env_var, temple.constants.TEMPLE_DOCS_URL)
            raise temple.exceptions.InvalidEnvironmentError(msg)


def is_temple_project():
    """Raises `InvalidTempleProjectError` if repository is not a temple project"""
    if not os.path.exists(temple.constants.TEMPLE_CONFIG_FILE):
        msg = 'No {} file found in repository.'.format(temple.constants.TEMPLE_CONFIG_FILE)
        raise temple.exceptions.InvalidTempleProjectError(msg)
