temple - Templated project management
#####################################

Temple provides templated project creation and management.

The main functionality of temple includes:

1. Creating new projects from `cookiecutter`_ templates.
2. Listing all available templates under a github user / org along with all projects created from
   those templates.
3. Keeping projects up to date with the template as it changes.

Documentation
=============

`View the temple docs here <http://temple.readthedocs.io/>`_.
A quick start and installation overview is provied below.

Installation
============

temple can be installed with::

    pip3 install temple

Most temple functionality requires a ``GITHUB_API_TOKEN`` environment variable to be set.
The Github API token is a personal token that you create
by following the `Github Access Token Instructions`_.
This token only requires ``repo`` scope.

.. _Github Access Token Instructions: https://help.github.com/articles/creating-an-access-token-for-command-line-use/

.. note::

    Temple requires a Github API token for listing available templates, starting new projects, and updating a project
    with a template. However, project templates themselves might have other setup requirements. Consult the documentation
    of templates you want to use for your projects for information about other installation and setup required.

Quick Start
===========

Projects are setup by temple with::

    temple setup <git@github.com:user/cookiecutter-template.git>

Temple uses `cookiecutter`_ to gather user input and
create the initial project scaffolding. `cookiecutter hooks`_ can be used to
do additional project setup, such as publishing it to a remote Github repository or configuring continuous
integration.

Once a project is set up and published to Github, temple-created projects can be listed with the ``temple ls``
command. ``temple ls <github_user_or_org>`` will list all available templates under a Github user or org.
``temple ls <github_user_or_org> <git@github.com:user/cookiecutter-template.git>`` will list all projects
created using a particular template. Note that ``temple ls -l`` will print off descriptions of the returned
repositories.

If a template is ever updated, changes can be pulled into a project with::

    temple update

This will diff the changes in the new template and apply them to your repository. You will have to add and
push these changes yourself. Note to lookout for "\*.rej" files after updating. These are lines that could
not automatically be applied to your repository, and you should look into them to see if they should be
applied.

Note that ``temple update --check`` can be used to check if the project is up to date with the latest template.

Contributing Guide
==================

For information on setting up temple for development and contributing changes, view `CONTRIBUTING.rst <CONTRIBUTING.rst>`_.


.. _Github Access Token Instructions: https://help.github.com/articles/creating-an-access-token-for-command-line-use/
.. _cookiecutter: https://cookiecutter.readthedocs.io/en/latest/
.. _cookiecutter hooks: http://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html

Primary Authors
===============

- @wesleykendall (Wes Kendall)
- @gwax (George Leslie-Waksman)

Other contributors can be found in the AUTHORS file
