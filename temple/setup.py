"""
temple.setup
~~~~~~~~~~~~

Creates and initializes a project from a template
"""
import subprocess
import unittest.mock

import cookiecutter.generate as cc_generate
import cookiecutter.hooks as cc_hooks

import temple.check
import temple.constants
import temple.utils


def _patched_run_hook(hook_name, project_dir, context):
    """Used to patch cookiecutter's ``run_hook`` function.

    This patched version ensures that the temple.yaml file is created before
    any cookiecutter hooks are executed
    """
    if hook_name == 'post_gen_project':
        with temple.utils.cd(project_dir):
            temple.utils.write_temple_config(context['cookiecutter'],
                                             context['template'],
                                             context['version'])
    return cc_hooks.run_hook(hook_name, project_dir, context)


def _generate_files(repo_dir, config, template, version):
    """Uses cookiecutter to generate files for the project.

    Monkeypatches cookiecutter's "run_hook" to ensure that the temple.yaml file is
    generated before any hooks run. This is important to ensure that hooks can also
    perform any actions involving temple.yaml
    """
    with unittest.mock.patch('cookiecutter.generate.run_hook', side_effect=_patched_run_hook):
        cc_generate.generate_files(repo_dir=repo_dir,
                                   context={'cookiecutter': config,
                                            'template': template,
                                            'version': version},
                                   overwrite_if_exists=False,
                                   output_dir='.')


@temple.utils.set_cmd_env_var('setup')
def setup(template, version=None):
    """Sets up a new project from a template

    Note that the `temple.constants.TEMPLE_ENV_VAR` is set to 'setup' during the duration
    of this function.

    Args:
        template (str): The git SSH path to a template
        version (str, optional): The version of the template to use when updating. Defaults
            to the latest version
    """
    temple.check.is_git_ssh_path(template)
    temple.check.not_in_git_repo()

    repo_path = temple.utils.get_repo_path(template)
    msg = (
        'You will be prompted for the parameters of your new project.'
        ' Please read the docs at https://github.com/{} before entering parameters.'
    ).format(repo_path)
    print(msg)

    cc_repo_dir, config = temple.utils.get_cookiecutter_config(template, version=version)

    if not version:
        with temple.utils.cd(cc_repo_dir):
            ret = temple.utils.shell('git rev-parse HEAD', stdout=subprocess.PIPE)
            version = ret.stdout.decode('utf-8').strip()

    _generate_files(repo_dir=cc_repo_dir, config=config, template=template, version=version)
