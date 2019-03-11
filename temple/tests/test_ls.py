"""Tests for temple.ls module"""
import collections
import urllib

import pytest
import requests

import temple.exceptions
from temple import constants
from temple import ls


@pytest.mark.parametrize('headers, expected_links', [
    ({'no_link_keys': 'value'}, {}),
    ({'link': '<https://url.com>; rel="next", <https://url2.com>; rel="last"'},
     {'next': 'https://url.com', 'last': 'https://url2.com'}),
])
def test_parse_link_header(headers, expected_links):
    """Tests ls._parse_link_header"""
    assert ls._parse_link_header(headers) == expected_links


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

    query = 'user:user {} in:path "template_path" in:file'.format(constants.TEMPLE_CONFIG_FILE)
    repos = ls._code_search(query)

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

    repos = ls._code_search('query')

    assert repos == {
        'git@github.com:repo/repo1.git': {'full_name': 'repo/repo1'},
        'git@github.com:repo/repo2.git': {'full_name': 'repo/repo2'},
        'git@github.com:repo/repo3.git': {'full_name': 'repo/repo3'},
        'git@github.com:repo/repo4.git': {'full_name': 'repo/repo4'},
    }


def test_code_search_invalid_github_user(mocker, responses):
    """Tests ls.ls when the github user is invalid"""
    responses.add(responses.GET, 'https://api.github.com/search/code',
                  status=requests.codes.unprocessable_entity, json={})

    query = 'user:user {} in:path "template_path" in:file'.format(constants.TEMPLE_CONFIG_FILE)
    with pytest.raises(temple.exceptions.InvalidGithubUserError):
        ls._code_search(query, github_user='invalid')


@pytest.mark.parametrize('template, github_query', [
    (None, 'user:u cookiecutter.json in:path'),
    ('git@github.com:u/t.git', 'user:u filename:temple.yaml git@github.com:u/t.git'),
])
def test_ls(template, github_query, mocker):
    mock_code_search = mocker.patch('temple.ls._code_search', autospec=True, return_value={
        'repo2': {'description': 'description 2'},
        'repo1': {'description': 'description 1'},
    })

    results = ls.ls('u', template=template)

    mock_code_search.assert_called_once_with(github_query, github_user='u')
    assert results == collections.OrderedDict([
        ('repo1', {'description': 'description 1'}),
        ('repo2', {'description': 'description 2'}),
    ])
