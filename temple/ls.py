"""
temple.ls
~~~~~~~~~

Lists all temple templates and projects spun up with those templates
"""
import temple.forge


@temple.utils.set_cmd_env_var('ls')
def ls(forge, template=None):
    """Lists all templates under a root path or list all projects spun up under
    a root path and a template path.

    The ``root`` path must be either a Github organization/user (e.g. github.com/organization)
    or a Gitlab group (e.g. gitlab.com/my/group).

    Note that the `temple.constants.TEMPLE_ENV_VAR` is set to 'ls' for the duration of this
    function.

    Args:
        root (str): A root git storage path.  For example, a Github organization
            (github.com/Organization) or a gitlab group (gitlab.com/my/group).
        template (str, default=None): An optional template path. If provided, the
            returned values are projects under ``root`` created using the template.

    Returns:
        dict: A dictionary of repository information keyed on the url.

    Raises:
        `InvalidRootError`: When ``root`` is invalid
    """
    client = temple.forge.from_path(forge)
    return client.ls(forge, template)