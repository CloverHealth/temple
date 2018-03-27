"""Tests for temple.update module"""
import subprocess

import pytest
from requests import codes as http_codes
import requests

import temple.constants
import temple.update


@pytest.mark.parametrize(
    'old_config, new_config, old_http_status, new_http_status, expected_has_changed',
    [
        ('{"config": "same"}', '{"config": "same"}', http_codes.ok, http_codes.ok, False),
        ('{"config": "same"}', '{"config": "diff"}', http_codes.ok, http_codes.ok, True),
        pytest.mark.xfail(('', '', http_codes.not_found, http_codes.ok, None),
                          raises=requests.exceptions.HTTPError),
        pytest.mark.xfail(('', '', http_codes.ok, http_codes.not_found, None),
                          raises=requests.exceptions.HTTPError),
    ])
def test_cookiecutter_configs_have_changed(old_config,
                                           new_config,
                                           old_http_status,
                                           new_http_status,
                                           expected_has_changed,
                                           mocker,
                                           responses):
    """Tests temple.update._cookiecutter_configs_have_changed"""
    api = 'https://api.github.com/repos/org/template/contents/cookiecutter.json'
    responses.add(responses.GET,
                  '{}?ref=old'.format(api),
                  json={'content': old_config},
                  status=old_http_status,
                  match_querystring=True)
    responses.add(responses.GET,
                  '{}?ref=new'.format(api),
                  json={'content': new_config},
                  status=new_http_status,
                  match_querystring=True)

    template = 'git@github.com:org/template.git'
    config_has_changed = temple.update._cookiecutter_configs_have_changed(template, 'old', 'new')
    assert config_has_changed == expected_has_changed


@pytest.mark.parametrize('http_status', [
    http_codes.ok,
    pytest.mark.xfail(http_codes.not_found, raises=requests.exceptions.HTTPError),
])
def test_get_latest_template_version_w_git_api(http_status, mocker, responses):
    """Tests temple.update._get_latest_template_version_w_git_api"""
    api = 'https://api.github.com/repos/owner/template/commits'
    responses.add(responses.GET, api, json=[{'sha': 'v1'}], status=http_status)

    latest = temple.update._get_latest_template_version_w_git_api(
        'git@github.com:owner/template.git')
    assert latest == 'v1'


@pytest.mark.parametrize('stdout, stderr, expected', [
    (b'version\n', b'', 'version'),
    (b'version\n', b'stderr_can_be_there_w_stdout', 'version'),
    pytest.mark.xfail((b'\n', b'stderr_w_no_stdout_is_an_error', None), raises=RuntimeError),
])
def test_get_latest_template_version_w_git_ssh(mocker, stdout, stderr, expected):
    """Tests temple.update._get_latest_template_version_w_git_ssh"""
    ls_remote_return = subprocess.CompletedProcess([], returncode=0, stdout=stdout,
                                                   stderr=stderr)
    mock_shell = mocker.patch('temple.utils.shell',
                              autospec=True,
                              return_value=ls_remote_return)

    assert temple.update._get_latest_template_version_w_git_ssh('t') == expected
    cmd = 'git ls-remote t | grep HEAD | cut -f1'
    mock_shell.assert_called_once_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize('git_ssh_side_effect, git_api_side_effect, expected', [
    (['version'], None, 'version'),
    (subprocess.CalledProcessError(returncode=1, cmd='cmd'), ['version'], 'version'),
    pytest.mark.xfail(
        (subprocess.CalledProcessError(returncode=1, cmd='cmd'),
         requests.exceptions.RequestException,
         None),
        raises=temple.exceptions.CheckRunError),
    pytest.mark.xfail(
        (subprocess.CalledProcessError(returncode=1, cmd='cmd'),
         temple.exceptions.InvalidEnvironmentError,
         None),
        raises=temple.exceptions.CheckRunError),
])
def test_get_latest_template_version(mocker, git_ssh_side_effect, git_api_side_effect, expected):
    mocker.patch('temple.update._get_latest_template_version_w_git_ssh',
                 autospec=True, side_effect=git_ssh_side_effect)
    mocker.patch('temple.update._get_latest_template_version_w_git_api',
                 autospec=True, side_effect=git_api_side_effect)

    version = temple.update._get_latest_template_version('template')
    assert version == expected


@pytest.mark.parametrize('existing_files', [True, False])
def test_apply_template(mocker, existing_files):
    mock_td = mocker.patch('tempfile.TemporaryDirectory', autospec=True)
    mock_cc = mocker.patch('cookiecutter.main.cookiecutter',
                           autospec=True, return_value='basepath')
    mock_list = mocker.patch('os.listdir', autospec=True, return_value=['a', 'b'])
    mocker.patch('os.path.isdir', autospec=True, side_effect=[True, False])
    mocker.patch('os.path.exists', autospec=True, return_value=existing_files)
    mock_shutil_ct = mocker.patch('shutil.copytree', autospec=True)
    mock_shutil_cp = mocker.patch('shutil.copy2', autospec=True)
    mock_rmtree = mocker.patch('shutil.rmtree', autospec=True)
    mock_remove = mocker.patch('os.remove', autospec=True)

    temple.update._apply_template('t', '.', checkout='v1', extra_context={'c': 'tx'})

    mock_cc.assert_called_once_with(
        't',
        checkout='v1',
        no_input=True,
        output_dir=mock_td.return_value.__enter__.return_value,
        extra_context={'c': 'tx'})
    mock_list.assert_called_once_with(mock_cc.return_value)
    mock_shutil_ct.assert_called_once_with('basepath/a', './a')
    mock_shutil_cp.assert_called_once_with('basepath/b', './b')
    if existing_files:
        mock_rmtree.assert_called_once_with('./a')
        mock_remove.assert_called_once_with('./b')
    else:
        assert not mock_rmtree.called
        assert not mock_remove.called


@pytest.mark.parametrize('temple_config, latest_version, supplied_version, expected_up_to_date', [
    ({'_version': 'v1', '_template': 't'}, 'v2', None, False),
    ({'_version': 'v1', '_template': 't'}, 'v1', None, True),
    ({'_version': 'v1', '_template': 't'}, 'v1', 'v2', False),
    ({'_version': 'v3', '_template': 't'}, 'v1', 'v3', True),
])
def test_up_to_date(temple_config, latest_version, supplied_version, expected_up_to_date, mocker):
    """Tests temple.update.up_to_date"""
    mocker.patch('temple.check.in_git_repo', autospec=True)
    mocker.patch('temple.check.in_clean_repo', autospec=True)
    mocker.patch('temple.check.is_temple_project', autospec=True)
    mocker.patch('temple.utils.read_temple_config',
                 autospec=True,
                 return_value=temple_config)
    mocker.patch('temple.update._get_latest_template_version',
                 autospec=True,
                 return_value=latest_version)

    assert temple.update.up_to_date(version=supplied_version) == expected_up_to_date


@pytest.mark.parametrize('version, supplied_version, latest_version', [
    ('v1', None, 'v1'),
    ('v1', 'v1', 'v0'),
])
def test_update_w_up_to_date(version, supplied_version, latest_version, mocker):
    """Tests temple.update.update when the template is already up to date"""
    mocker.patch('temple.check.not_has_branch', autospec=True)
    mocker.patch('temple.check.in_git_repo', autospec=True)
    mocker.patch('temple.check.in_clean_repo', autospec=True)
    mocker.patch('temple.check.is_temple_project', autospec=True)
    mocker.patch('temple.utils.read_temple_config',
                 autospec=True,
                 return_value={'_version': version, '_template': 't'})
    mocker.patch('temple.update._get_latest_template_version',
                 autospec=True,
                 return_value=latest_version)

    assert not temple.update.update(new_version=supplied_version)


@pytest.mark.parametrize(
    'cc_configs_changed, enter_parameters, current_version, latest_version, old_template',
    [
        (False, False, 'v1', 'v2', None),
        (False, False, 'v1', 'v2', 'git@github.com:owner/old_repo.git'),
        (True, False, 'v1', 'v2', None),
        (False, True, 'v1', 'v2', None),
        # Updates should still proceed when entering parameters and up to date with latest
        (False, True, 'v1', 'v1', None),
    ])
def test_update_w_out_of_date(cc_configs_changed, enter_parameters,
                              current_version, latest_version, old_template,
                              mocker, fs):
    """Tests temple.update.update when the template is out of date"""
    template = 'git@github.com:owner/repo.git'
    temple_config = {'_version': current_version, '_template': template}
    mocker.patch('temple.check.in_git_repo', autospec=True)
    mocker.patch('temple.check.in_clean_repo', autospec=True)
    mocker.patch('temple.check.is_temple_project', autospec=True)
    mocker.patch('temple.check.not_has_branch', autospec=True)
    mocker.patch('temple.utils.read_temple_config',
                 autospec=True,
                 return_value=temple_config)
    mocker.patch('temple.update._get_latest_template_version',
                 autospec=True,
                 return_value=latest_version)
    mock_apply_template = mocker.patch('temple.update._apply_template', autospec=True)
    mock_cc_configs_have_changed = mocker.patch('temple.update._cookiecutter_configs_have_changed',
                                                autospec=True,
                                                return_value=cc_configs_changed)
    mock_input = mocker.patch('builtins.input', autospec=True)
    mock_get_cc_config = mocker.patch('temple.utils.get_cookiecutter_config',
                                      autospec=True,
                                      return_value=('repo', temple_config))
    mock_shell = mocker.patch('temple.utils.shell', autospec=True)
    mock_write_config = mocker.patch('temple.utils.write_temple_config', autospec=True)

    temple.update.update(enter_parameters=enter_parameters, old_template=old_template)

    assert mock_input.called == cc_configs_changed or old_template is not None
    assert mock_get_cc_config.called == (
        cc_configs_changed or enter_parameters or old_template is not None)
    assert mock_apply_template.call_args_list == [
        mocker.call(old_template or template,
                    '.',
                    checkout=current_version,
                    extra_context=temple_config),
        mocker.call(template,
                    '.',
                    checkout=latest_version,
                    extra_context=temple_config),
    ]
    mock_write_config.assert_called_once_with(temple_config, template, latest_version)
    if not old_template:
        mock_cc_configs_have_changed.assert_called_once_with(template, current_version,
                                                             latest_version)
    else:
        assert not mock_cc_configs_have_changed.called

    assert mock_shell.call_args_list == [
        mocker.call('git checkout -b _temple_update',
                    stderr=subprocess.DEVNULL),
        mocker.call('git checkout --orphan _temple_update_temp',
                    stderr=subprocess.DEVNULL),
        mocker.call('git rm -rf .',
                    stdout=subprocess.DEVNULL),
        mocker.call('git add .'),
        mocker.call('git commit --no-verify -m "Initialize template from version {}"'
                    .format(current_version),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL),
        mocker.call('git checkout _temple_update',
                    stderr=subprocess.DEVNULL),
        mocker.call('git merge -s ours --no-edit --allow-unrelated-histories '
                    '_temple_update_temp',
                    stderr=subprocess.DEVNULL),
        mocker.call('git checkout _temple_update_temp',
                    stderr=subprocess.DEVNULL),
        mocker.call('git rm -rf .',
                    stdout=subprocess.DEVNULL),
        mocker.call('git add .'),
        mocker.call('git commit --no-verify -m "Update template to version {}"'
                    .format(latest_version),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL),
        mocker.call('git checkout _temple_update',
                    stderr=subprocess.DEVNULL),
        mocker.call('git merge --no-commit _temple_update_temp',
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL),
        mocker.call('git checkout --theirs temple.yaml',
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL),
        mocker.call('git branch -D _temple_update_temp',
                    stdout=subprocess.DEVNULL),
    ]
