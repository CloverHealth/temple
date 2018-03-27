"""
The temple CLI contains commands for setting up, listing, and updating projects.

Commands
~~~~~~~~

* ``temple setup`` - Sets up a new project
* ``temple ls`` - Lists all templates and projects created with those templates
* ``temple update`` - Updates the project to the latest template version
* ``temple clean`` - Cleans up any temporary resources used by temple
"""
import click

import temple
import temple.clean
import temple.exceptions
import temple.ls
import temple.setup
import temple.update


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Show version')
def main(ctx, version):
    if version:
        print('temple {}'.format(temple.__version__))
    elif not ctx.invoked_subcommand:
        print(ctx.get_help())


@main.command()
@click.argument('template', nargs=1, required=True)
@click.option('-v', '--version', default=None,
              help='Git SHA or branch of template to use for creation')
def setup(template, version):
    """
    Setup new project. Takes a full git SSH path to the template as returned
    by "temple ls". In order to start a project from a
    particular version (instead of the latest), use the "-v" option.
    """
    temple.setup.setup(template, version=version)


@main.command()
@click.option('-c', '--check', is_flag=True,
              help='Check to see if up to date')
@click.option('-e', '--enter-parameters', is_flag=True,
              help='Enter template parameters on update')
@click.option('-v', '--version', default=None,
              help='Git SHA or branch of template to use for update')
def update(check, enter_parameters, version):
    """
    Update package with latest template. Must be inside of the project
    folder to run.

    Using "-e" will prompt for re-entering the template parameters again
    even if the project is up to date.

    Use "-v" to update to a particular version of a template.

    Using "-c" will perform a check that the project is up to date
    with the latest version of the template (or the version specified by "-v").
    No updating will happen when using this option.
    """
    if check:
        if temple.update.up_to_date(version=version):
            print('Temple package is up to date')
        else:
            msg = (
                'This temple package is out of date with the latest template.'
                ' Update your package by running "temple update" and commiting changes.'
            )
            raise temple.exceptions.NotUpToDateWithTemplateError(msg)
    else:
        temple.update.update(new_version=version, enter_parameters=enter_parameters)


@main.command()
@click.argument('github_user', nargs=1, required=True)
@click.argument('template', nargs=1, required=False)
@click.option('-l', '--long-format', is_flag=True,
              help='Print extended information about results')
def ls(github_user, template, long_format):
    """
    List packages created with temple. Enter a github user or
    organization to list all templates under the user or org.
    Using a template path as the second argument will list all projects
    that have been started with that template.

    Use "-l" to print the Github repository descriptions of templates
    or projects.
    """
    github_urls = temple.ls.ls(github_user, template=template)
    for ssh_path, info in github_urls.items():
        if long_format:
            print(ssh_path, '-', info['description'] or '(no project description found)')
        else:
            print(ssh_path)


@main.command()
def clean():
    """
    Cleans temporary resources created by temple, such as the temple update branch
    """
    temple.clean.clean()


@main.command()
@click.argument('template', nargs=1, required=True)
@click.option('-v', '--version', default=None,
              help='Git SHA or branch of template to use for update')
def switch(template, version):
    """
    Switch a project's template to a different template.
    """
    temple.update.update(new_template=template, new_version=version)
