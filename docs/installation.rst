.. _installation:


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
