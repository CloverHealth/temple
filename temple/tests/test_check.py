"""Tests for temple.check module"""
import os
import subprocess

import pytest

import temple.check
import temple.constants
import temple.exceptions


def test_is_git_ssh_path_valid():
    temple.check.is_git_ssh_path('git@github.com:user/template.git')


def test_get_name_from_ssh_path():
    assert temple.check.get_name_from_ssh_path('git@github.com:user/template.git') == "template"
    assert temple.check.get_name_from_ssh_path('git@github.com:user/foo-bar.git') == "foo-bar"
    assert temple.check.get_name_from_ssh_path('git@github.com:user/foo_bar1.git') == "foo_bar1"


@pytest.mark.parametrize('invalid_template_path', [
    'bad_path',
    'git@github.com:user/template',
    '',
    'abc@def.com:user/template.git',
])
def test_is_git_ssh_path_invalid(invalid_template_path):
    with pytest.raises(temple.exceptions.InvalidTemplatePathError):
        temple.check.is_git_ssh_path(invalid_template_path)


@pytest.mark.parametrize('revparse_returncode', [
    pytest.param(255, marks=pytest.mark.xfail(raises=temple.exceptions.NotInGitRepoError)),
    0,
])
def test_in_git_repo(revparse_returncode, mocker):
    """Tests temple.check.not_in_git_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('temple.utils.shell', autospec=True, return_value=revparse_return)

    assert temple.check.in_git_repo() is None

    mock_shell.assert_called_once_with('git rev-parse', stderr=subprocess.DEVNULL, check=False)


@pytest.mark.parametrize('revparse_returncode', [
    255,
    pytest.param(0, marks=pytest.mark.xfail(raises=temple.exceptions.InGitRepoError)),
])
def test_not_in_git_repo(revparse_returncode, mocker):
    """Tests temple.check.not_in_git_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('temple.utils.shell', autospec=True, return_value=revparse_return)

    assert temple.check.not_in_git_repo() is None

    mock_shell.assert_called_once_with('git rev-parse', stderr=subprocess.DEVNULL, check=False)


@pytest.mark.parametrize('revparse_returncode', [
    0,
    pytest.param(255, marks=pytest.mark.xfail(raises=temple.exceptions.InDirtyRepoError)),
])
def test_in_clean_repo(revparse_returncode, mocker):
    """Tests temple.check.in_clean_repo"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('temple.utils.shell', autospec=True, return_value=revparse_return)

    assert temple.check.in_clean_repo() is None

    mock_shell.assert_called_once_with('git diff-index --quiet HEAD --', check=False)


@pytest.mark.parametrize('revparse_returncode', [
    128,
    pytest.param(0, marks=pytest.mark.xfail(raises=temple.exceptions.ExistingBranchError)),
])
def test_not_has_branch(revparse_returncode, mocker):
    """Tests temple.check.not_has_branch"""
    revparse_return = subprocess.CompletedProcess([], returncode=revparse_returncode)
    mock_shell = mocker.patch('temple.utils.shell', autospec=True, return_value=revparse_return)

    assert temple.check.not_has_branch('somebranch') is None

    mock_shell.assert_called_once_with('git rev-parse --verify somebranch',
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,
                                       check=False)


@pytest.mark.parametrize('envvar_names, check_envvar_names', [
    pytest.param(['v1', 'v2'], ['v2', 'v3'],
                 marks=pytest.mark.xfail(raises=temple.exceptions.InvalidEnvironmentError)),
    pytest.param([], ['v2'], marks=pytest.mark.xfail(
        raises=temple.exceptions.InvalidEnvironmentError)),
    (['v2'], ['v2']),
    (['v1', 'v2'], ['v1', 'v2']),
])
def test_has_env_vars(envvar_names, check_envvar_names, mocker):
    """Tests temple.check.has_circleci_api_token"""
    mocker.patch.dict(os.environ, {var_name: 'value' for var_name in envvar_names}, clear=True)

    assert temple.check.has_env_vars(*check_envvar_names) is None


@pytest.mark.parametrize('temple_file', [
    pytest.param('regular_file', marks=pytest.mark.xfail(
        raises=temple.exceptions.InvalidTempleProjectError)),
    temple.constants.TEMPLE_CONFIG_FILE,
])
def test_check_is_temple_project(temple_file, fs):
    """Tests update._check_is_temple_project"""
    fs.CreateFile(temple_file)

    assert temple.check.is_temple_project() is None
