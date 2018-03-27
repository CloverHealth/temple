"""
temple.exceptions
~~~~~~~~~~~~~~~~~

Temple exceptions
"""


class Error(Exception):
    """The top-level error for temple"""


class InGitRepoError(Error):
    """Thrown when running inside of a git repository"""


class NotInGitRepoError(Error):
    """Thrown when not running inside of a git repo"""


class InDirtyRepoError(Error):
    """Thrown when running in a dirty git repo"""


class InvalidTempleProjectError(Error):
    """Thrown when the repository was not created with temple"""


class NotUpToDateWithTemplateError(Error):
    """Thrown when a temple project is not up to date with the template"""


class CheckRunError(Error):
    """When running ``temple update --check`` errors"""


class InvalidEnvironmentError(Error):
    """Thrown when required environment variables are not set"""


class InvalidGithubUserError(Error):
    """An invalid github user was passed to ls."""


class InvalidTemplatePathError(Error):
    """Thrown when a template path is not a Github SSH path"""


class ExistingBranchError(Error):
    """Thrown when a specifically named branch exists or doesn't exist as expected."""


class InvalidCurrentBranchError(Error):
    """Thrown when a command cannot run because of the current git branch"""
