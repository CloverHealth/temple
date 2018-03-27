"""Tests for temple.setup module"""
import os
import subprocess

import pytest

import temple.constants
import temple.setup
import temple.exceptions


@pytest.mark.parametrize('version, expected_revparse_called, expected_version', [
    (None, True, 'latest_version'),
    ('version', False, 'version'),
])
def test_setup(version, expected_revparse_called, expected_version, mocker):
    """Tests temple.setup.setup_template"""
    config = {'my': 'config'}
    template = 'git@github.com:user/template.git'
    mocker.patch('temple.check.not_in_git_repo', autospec=True)
    mock_get_cc_config = mocker.patch('temple.utils.get_cookiecutter_config',
                                      autospec=True,
                                      return_value=('.', config))

    revparse_return = subprocess.CompletedProcess([], stdout=b'latest_version', returncode=0)
    mock_generate_files = mocker.patch('temple.setup.cc_generate.generate_files',
                                       autospec=True,
                                       return_value='.')
    mock_shell = mocker.patch('temple.utils.shell',
                              autospec=True,
                              side_effect=[revparse_return, None, None, None, None, None])

    temple.setup.setup(template, version=version)

    mock_get_cc_config.assert_called_once_with(template, version=version)
    mock_generate_files.assert_called_once_with(context={'cookiecutter': config,
                                                         'template': template,
                                                         'version': expected_version},
                                                output_dir='.',
                                                overwrite_if_exists=False,
                                                repo_dir='.')
    assert mock_shell.called == expected_revparse_called


def test_generate_files(tmpdir):
    """Generate files for a fake template created in a temporary directory"""
    template_dir = '%s/template' % tmpdir
    template_project_dir = '%s/{{cookiecutter.name}}' % template_dir
    hooks_dir = '%s/template/hooks' % tmpdir
    project_dir = '%s/project' % tmpdir

    os.mkdir(template_dir)
    os.mkdir(template_project_dir)
    os.mkdir(hooks_dir)
    with open('%s/cookiecutter.json' % template_dir, 'w') as config:
        config.write('{"name": null}')
    with open('%s/name.txt' % template_project_dir, 'w') as name:
        name.write('my name is {{cookiecutter.name}}')
    with open('%s/post_gen_project.sh' % hooks_dir, 'w') as hook:
        hook.write('#!/usr/bin/env sh\ntouch hook_file\n')
    os.chmod('%s/post_gen_project.sh' % hooks_dir, 0o700)

    with temple.utils.cd(str(tmpdir)):
        temple.setup._generate_files(repo_dir=template_dir,
                                     config={'name': 'project'},
                                     template='template',
                                     version='version')

    # Verify files were created properly
    with temple.utils.cd(project_dir):
        with open('name.txt') as name:
            assert name.read() == 'my name is project'
        config = temple.utils.read_temple_config()
        assert config == {'_template': 'template', '_version': 'version', 'name': 'project'}
        # The post_gen_project hook should have made this file
        assert os.path.exists('hook_file')
