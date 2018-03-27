"""Tests fr temple.utils module"""
import os
import subprocess

import pytest

import temple.constants
import temple.utils


@pytest.mark.parametrize('cmd, check, stdin, stdout, stderr', [
    ('cmd', True, subprocess.PIPE, subprocess.PIPE, subprocess.PIPE),
    ('cmd', False, None, None, None),
])
def test_shell(cmd, check, stdin, stdout, stderr, mocker):
    """Tests temple.utils.shell"""
    mock_run = mocker.patch('subprocess.run', autospec=True)

    temple.utils.shell(cmd, check=check, stdin=stdin, stdout=stdout, stderr=stderr)

    mock_run.assert_called_once_with(cmd,
                                     shell=True,
                                     check=check,
                                     stdin=stdin,
                                     stdout=stdout,
                                     stderr=stderr)


def test_cd(fs):
    """Tests temple.utils.cd using a fake filesystem"""
    os.mkdir('/tmp_dir')
    orig_cwd = os.getcwd()
    with temple.utils.cd('/tmp_dir'):
        assert os.getcwd() == '/tmp_dir'

    assert os.getcwd() == orig_cwd


def test_read_temple_config(fs):
    """Tests temple.utils.read_temple_config with a fake file system"""
    temple_config_yaml = (
        '_version: version\n'
        'repo_name: repo_name\n'
        '_extensions: [jinja2_time.TimeExtension]\n'
    )
    fs.CreateFile('temple.yaml', contents=temple_config_yaml)

    assert temple.utils.read_temple_config() == {
        '_version': 'version',
        'repo_name': 'repo_name',
        '_extensions': ['jinja2_time.TimeExtension'],
    }


def test_write_temple_config(fs):
    """Tests temple.utils.write_temple_config with a fake file system"""
    temple.utils.write_temple_config({
        'repo_name': 'repo_name',
        '_extensions': ['jinja2_time.TimeExtension'],
    }, template='t', version='version')

    with open(temple.constants.TEMPLE_CONFIG_FILE) as config:
        assert set(config.readlines()) == {
            '_extensions: [jinja2_time.TimeExtension]\n',
            '_template: t\n',
            '_version: version\n',
            'repo_name: repo_name\n',
        }


@pytest.mark.parametrize('default_config', [
    None,
    {'my': 'config'},
])
def test_get_cookiecutter_config(default_config, mocker):
    """Tests temple.utils.get_cookiecutter_config"""
    default_context = {'default': 'context'}
    generated_context = {'generated': 'context'}
    prompted_context = {'prompted': 'context'}

    mock_get_user_conf = mocker.patch('cookiecutter.config.get_user_config', autospec=True,
                                      return_value={
                                          'abbreviations': 'abbr',
                                          'cookiecutters_dir': 'cc_dir',
                                          'default_context': default_context,
                                      })
    mock_repo_dir = mocker.patch('cookiecutter.repository.determine_repo_dir', autospec=True,
                                 return_value=('repo_dir', True))
    mock_gen_context = mocker.patch('cookiecutter.generate.generate_context', autospec=True,
                                    return_value=generated_context)

    mock_prompt_for_conf = mocker.patch('cookiecutter.prompt.prompt_for_config', autospec=True,
                                        return_value=prompted_context)

    assert (
        temple.utils.get_cookiecutter_config('t', default_config=default_config) ==
        ('repo_dir', prompted_context)
    )
    mock_get_user_conf.assert_called_once_with()
    mock_repo_dir.assert_called_once_with(template='t',
                                          abbreviations='abbr',
                                          clone_to_dir='cc_dir',
                                          checkout=None,
                                          no_input=True)
    mock_gen_context.assert_called_once_with(context_file='repo_dir/cookiecutter.json',
                                             default_context={
                                                 **(default_config or {}),
                                                 **default_context,
                                             })
    mock_prompt_for_conf.assert_called_once_with(generated_context)


def test_set_cmd_env_var():
    """Tests temple.utils.set_cmd_env_var"""
    @temple.utils.set_cmd_env_var("value1")
    def func1():
        assert os.environ[temple.constants.TEMPLE_ENV_VAR] == 'value1'
        return 123

    @temple.utils.set_cmd_env_var("value2")
    def func2():
        assert os.environ[temple.constants.TEMPLE_ENV_VAR] == 'value2'
        raise NotImplementedError()

    assert temple.constants.TEMPLE_ENV_VAR not in os.environ
    assert func1() == 123
    assert temple.constants.TEMPLE_ENV_VAR not in os.environ
    with pytest.raises(NotImplementedError):
        func2()
    assert temple.constants.TEMPLE_ENV_VAR not in os.environ

    os.environ[temple.constants.TEMPLE_ENV_VAR] = 'testvalue'
    try:
        assert func1() == 123
        assert os.environ[temple.constants.TEMPLE_ENV_VAR] == 'testvalue'
        with pytest.raises(NotImplementedError):
            func2()
        assert os.environ[temple.constants.TEMPLE_ENV_VAR] == 'testvalue'
    finally:
        os.environ.pop(temple.constants.TEMPLE_ENV_VAR, None)
