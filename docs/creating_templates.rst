.. _creating_templates:

Creating Templates Managed by Temple
====================================

Under the hood, temple uses `cookiecutter <https://cookiecutter.readthedocs.io/en/latest/>`_ to gather user
input about a project and then spin up a local directory with the project scaffolding. In order to learn
more about how to make your own cookiecutter template, consult the `cookiecutter docs <https://cookiecutter.readthedocs.io/en/latest/>`_.

After you have created a template and published it to Github, it will be displayed with ``temple ls``
and can also be used by ``temple setup``. There is no additional setup required. Make sure the description of your repo is filled in
on Github, because that will be returned when users type ``temple ls -l``.

Making Project Creation Seamless with Cookiecutter Hooks
--------------------------------------------------------

Once you have created a cookiecutter template and published it to Github, it will work with temple out of the box, but there are
ways to make project setup even more seamless.

For example, say a cookiecutter template has been created at git@github.com:user/cookiecutter-template.git. When the user calls
``temple setup git@github.com:user/cookiecutter-template.git``, the templated project will be created locally, but the user will
be left to do remaining setup steps manually (like pushing to Github, setting up continuous integration, etc).

Cookiecutter offers the ability to insert `pre or post generate hooks <http://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html>`_
before and after a project is created, allowing project-specific setup steps to happen. Some of the examples given in the
`hook docs <http://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html>`_ include ensuring a python module name is valid.

Hooks can be used for initial project setup in a variety of ways, some examples including:

1. Creating a remote github repository for the project
2. Pushing to a remote github repository after the project is created
3. Adding default collaborators to a project
4. Setting up continuous integration for a project
5. Creating an initial server for a web app along with a domain name

Keep in mind that cookiecutter hooks are called during ``temple setup`` and ``temple update``. Although hooks should be idempotent in
the case of transient setup failures, sometimes it is not desirable to have hooks execute during ``setup`` and ``update``. In order
to customize this behavior in your hooks, temple exports the ``_TEMPLE`` environment variable and sets it to value of the command
being executed (i.e. "ls", "setup", or "update").

Below is an example of creating a ``pre_gen_project.py`` hook in the ``hooks`` directory of the template. The script ensures that
the cookiecutter template is only used by temple and not by ``cookiecutter`` or another templating library:

.. code:: python

    #!/usr/bin/env python

    import os

    if __name__ == "__main__":
        if not os.environ.get('_TEMPLE'):
            raise Exception('This template can only be used by temple')

Here's an example of pushing the newly-created project to github with a ``post_gen_project.py`` file:

.. code:: python

    #!/usr/bin/env python3

    import os
    import subprocess

    def call_cmd(cmd, check=True):
        """Call a command. If check=True, throw an error if command fails"""
        return subprocess.call(cmd, check=check)

    def push_to_github():
        call_cmd('git init')
        call_cmd('git add .')
        call_cmd('git commit -m "Initial project scaffolding"')
        # Use the "repo_name" template variable
        call_cmd('git remote add origin {repo_name}')
        ret = call_cmd('git push origin master', check=False)
        if ret.returncode != 0:
            # Do additional error handling if the repo already exists.
            # Maybe the user already created the remote repository..
            pass

    if __name__ == "__main__":
        # Only run these commands when "temple setup" is being called
        if os.environ.get('_TEMPLE') == 'setup':
            push_to_github()

In the above hook, the ``push_to_github`` function is called only when running ``temple setup``. In other words, this
hook code will not run on ``temple update`` or any other commands that invoke the template to be rendered.

As shown above, variables that are part of the template, like ``{repo_name}`` can be referenced and used in the hooks.
If the above fails, it will cause all of ``temple setup`` to fail, which will in turn not create any local project on
the user's machine. Idempotency of project hooks should be kept in mind when designing them.

.. note::

    The hooks shown can also be written in shell and named ``pre_gen_project.sh`` and ``post_gen_project.sh``.