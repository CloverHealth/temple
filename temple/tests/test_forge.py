"""Tests for temple.ls module"""
import collections
import subprocess
import urllib

import pytest
import requests
from requests import codes as http_codes

import temple.forge
import temple.constants
import temple.exceptions


@pytest.mark.parametrize('http_status', [
    http_codes.ok,
    pytest.param(http_codes.not_found,
                 marks=pytest.mark.xfail(raises=requests.exceptions.HTTPError)),
])
def test_github_get_latest_template_version(http_status, mocker, responses):
    """Tests temple.forge.Github._get_latest_template_version"""
    api = 'https://api.github.com/repos/owner/template/commits'
    responses.add(responses.GET, api, json=[{'sha': 'v1'}], status=http_status)

    latest = temple.forge.Github()._get_latest_template_version(
        'git@github.com:owner/template.git')
    assert latest == 'v1'


@pytest.mark.parametrize('stdout, stderr, expected', [
    (b'version\n', b'', 'version'),
    (b'version\n', b'stderr_can_be_there_w_stdout', 'version'),
    pytest.param(b'\n', b'stderr_w_no_stdout_is_an_error', None,
                 marks=pytest.mark.xfail(raises=RuntimeError)),
])
def test_get_latest_template_version_w_ssh(mocker, stdout, stderr, expected):
    """Tests temple.forge._get_latest_template_version_w_ssh"""
    ls_remote_return = subprocess.CompletedProcess([], returncode=0, stdout=stdout,
                                                   stderr=stderr)
    mock_shell = mocker.patch('temple.utils.shell',
                              autospec=True,
                              return_value=ls_remote_return)

    assert temple.forge._get_latest_template_version_w_ssh('t') == expected
    cmd = 'git ls-remote t | grep HEAD | cut -f1'
    mock_shell.assert_called_once_with(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize('git_ssh_side_effect, git_api_side_effect, expected', [
    (['version'], None, 'version'),
    (subprocess.CalledProcessError(returncode=1, cmd='cmd'), ['version'], 'version'),
    pytest.param(
        subprocess.CalledProcessError(returncode=1, cmd='cmd'),
        requests.exceptions.RequestException,
        None,
        marks=pytest.mark.xfail(raises=temple.exceptions.CheckRunError)),
    pytest.param(
        subprocess.CalledProcessError(returncode=1, cmd='cmd'),
        temple.exceptions.InvalidEnvironmentError,
        None,
        marks=pytest.mark.xfail(raises=temple.exceptions.CheckRunError)),
])
def test_get_latest_template_version(mocker, git_ssh_side_effect, git_api_side_effect, expected):
    mocker.patch('temple.forge._get_latest_template_version_w_ssh',
                 autospec=True, side_effect=git_ssh_side_effect)
    mocker.patch.object(temple.forge.Github, '_get_latest_template_version',
                 autospec=True, side_effect=git_api_side_effect)

    version = temple.forge.Github().get_latest_template_version('template')
    assert version == expected


@pytest.mark.parametrize(
    'root, expected_client_cls', [
        ('github.com/user', temple.forge.Github),
        pytest.param('invalid', None, marks=pytest.mark.xfail(raises=temple.exceptions.InvalidRootError)),
    ]
)
def test_get_client(root, expected_client_cls):
    client = temple.forge.from_path(root)
    assert client.__class__ == expected_client_cls


@pytest.mark.parametrize('headers, expected_links', [
    ({'no_link_keys': 'value'}, {}),
    ({'link': '<https://url.com>; rel="next", <https://url2.com>; rel="last"'},
     {'next': 'https://url.com', 'last': 'https://url2.com'}),
])
def test_parse_link_header(headers, expected_links):
    """Tests ls._parse_link_header"""
    assert temple.forge.Github()._parse_link_header(headers) == expected_links


def test_code_search_single_page(mocker, responses):
    """Tests ls.ls for a single page of responses"""
    response_content = {
        'items': [{
            'repository': {
                'full_name': 'repo/repo1',
            },
        }, {
            'repository': {
                'full_name': 'repo/repo2',
            },
        }],
    }
    responses.add(responses.GET, 'https://api.github.com/search/code',
                  status=requests.codes.ok, json=response_content)

    query = 'user:user {} in:path "template_path" in:file'.format(temple.constants.TEMPLE_CONFIG_FILE)
    repos = temple.forge.Github()._code_search(query)

    assert repos == {
        'git@github.com:repo/repo1.git': {'full_name': 'repo/repo1'},
        'git@github.com:repo/repo2.git': {'full_name': 'repo/repo2'},
    }
    assert len(responses.calls) == 1
    url = urllib.parse.urlparse(responses.calls[0].request.url)
    parsed_query = urllib.parse.parse_qs(url.query)
    assert parsed_query == {
        'per_page': ['100'],
        'q': [query],
    }


def test_code_search_multiple_pages(mocker, responses):
    """Tests ls.ls for a single page of responses"""
    response_content1 = {
        'items': [{
            'repository': {
                'full_name': 'repo/repo1',
            },
        }, {
            'repository': {
                'full_name': 'repo/repo2',
            },
        }],
    }
    response_link_header1 = {
        'link': '<https://next_url.com>; rel="next", <https://next_url2.com>; rel="last"',
    }
    response_content2 = {
        'items': [{
            'repository': {
                'full_name': 'repo/repo3',
            },
        }, {
            'repository': {
                'full_name': 'repo/repo4',
            },
        }],
    }
    responses.add(responses.GET, 'https://api.github.com/search/code',
                  status=requests.codes.ok, json=response_content1,
                  adding_headers=response_link_header1)
    responses.add(responses.GET, 'https://next_url.com',
                  status=requests.codes.ok, json=response_content2)

    repos = temple.forge.Github()._code_search('query')

    assert repos == {
        'git@github.com:repo/repo1.git': {'full_name': 'repo/repo1'},
        'git@github.com:repo/repo2.git': {'full_name': 'repo/repo2'},
        'git@github.com:repo/repo3.git': {'full_name': 'repo/repo3'},
        'git@github.com:repo/repo4.git': {'full_name': 'repo/repo4'},
    }


@pytest.mark.parametrize(
    'ssh_path, expected_name', [
        ('git@github.com:user/template.git', 'template'),
        ('git@github.com:user/foo-bar.git', 'foo-bar'),
        ('git@github.com:user/foo_bar1.git', 'foo_bar1')
    ]
)
def test_get_name_from_ssh_path(ssh_path, expected_name):
    assert temple.forge.get_name_from_ssh_path(ssh_path) == expected_name


def test_code_search_invalid_root(mocker, responses):
    """Tests ls.ls when the root is invalid"""
    responses.add(responses.GET, 'https://api.github.com/search/code',
                  status=requests.codes.unprocessable_entity, json={})

    query = 'user:user {} in:path "template_path" in:file'.format(temple.constants.TEMPLE_CONFIG_FILE)
    with pytest.raises(temple.exceptions.InvalidRootError):
        temple.forge.Github()._code_search('invalid', query)
