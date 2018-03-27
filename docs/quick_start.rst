Quick Start
-----------

Listing templates and projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Temple manages projects that are started from templates
(specifically, `cookiecutter`_ templates).
In order to see what templates are available for use within your Github org, do::

    temple ls <github_org_name>

This will list all of the paths of templates that are available. Doing::

    temple ls <github_org_name> -l

will also display the description of the template.

To list all projects created with a template (and the project's descriptions), take the
template path from ``temple ls`` and use it as an argument like so::

    temple ls <github_org_name> <git@github.com:user/cookiecutter-template.git> -l

Starting new projects
~~~~~~~~~~~~~~~~~~~~~

A new project can be set up from a template with::

    temple setup <git@github.com:user/cookiecutter-template.git>

What happens next is dependent on how the template is configured. By default, `cookiecutter`_ will
prompt the user for template parameters, defined in the ``cookiecutter.json`` file of the template
repository. If any `cookiecutter hooks`_ are defined in the project, additional setup steps will
happen that are specific to the type of project being started.

Keeping your project up to date with the latest template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once a project is set up and published to Github, temple-created projects can be listed with the ``temple ls``
command. If a template is ever updated, changes can be pulled into a project with::

    temple update

This will git merge the template changes into your repository. You will need to review the changes, resolve
conflicts, and then ``git add`` and ``git push`` these changes yourself.

Sometimes it is desired that projects always remain up to date with the latest template - for example, ensuring
that each project obtains a security patch to a dependency or doing an organization-wide upgrade to a new
version of Python.

Using ``temple update --check`` from the repository will succeed if the project is up to date with the latest
template or return a non-zero exit code if it isn't. This command can be executed as part of automated testing
that happens in continuous integration in order to ensure all projects remain up to date with changes before
being deployed.

.. note::

	Updating your project with the latest template does not result in `cookiecutter hooks`_ being executed again.

Switching your project to another template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes it is desirable to switch a project to another template, like when open sourcing a private package.
Projects can be switched to another template with::

	temple switch <git@github.com/user/new-template-path.git>

Similar to ``temple update``, you will need to review the changes, resolve conflicts, and then ``git add`` and
``git push`` these changes.

.. note::

	Switching templates does not trigger any `cookiecutter hooks`_. Users must manually do any project setup
	and must similarly do any project teardown that might have resulted from the previously template. The
	authors have intentionally left out this convenience for now since temple currently has no way to spin down projects.


.. _cookiecutter: https://cookiecutter.readthedocs.io/en/latest/
.. _cookiecutter hooks: http://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html
