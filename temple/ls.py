"""
temple.ls
~~~~~~~~~

Lists all temple templates and projects spun up with those templates
"""
import collections

import requests

import temple.check
import temple.constants
import temple.utils


def _parse_link_header(headers):
    """Parses Github's link header for pagination.

    TODO eventually use a github client for this
    """
    links = {}
    if 'link' in headers:
        link_headers = headers['link'].split(', ')
        for link_header in link_headers:
            (url, rel) = link_header.split('; ')
            url = url[1:-1]
            rel = rel[5:-1]
            links[rel] = url
    return links


def _code_search(query, github_user=None):
    """Performs a Github API code search

    Args:
        query (str): The query sent to Github's code search
        github_user (str, optional): The Github user being searched in the query string

    Returns:
        dict: A dictionary of repository information keyed on the git SSH url

    Raises:
        `InvalidGithubUserError`: When ``github_user`` is invalid
    """
    github_client = temple.utils.GithubClient()
    headers = {'Accept': 'application/vnd.github.v3.text-match+json'}

    resp = github_client.get('/search/code',
                             params={'q': query, 'per_page': 100},
                             headers=headers)

    if resp.status_code == requests.codes.unprocessable_entity and github_user:
        raise temple.exceptions.InvalidGithubUserError(
            'Invalid Github user or org - "{}"'.format(github_user))
    resp.raise_for_status()

    resp_data = resp.json()

    repositories = collections.defaultdict(dict)
    while True:
        repositories.update({
            'git@github.com:{}.git'.format(repo['repository']['full_name']): repo['repository']
            for repo in resp_data['items']
        })

        next_url = _parse_link_header(resp.headers).get('next')
        if next_url:
            resp = requests.get(next_url, headers=headers)
            resp.raise_for_status()
            resp_data = resp.json()
        else:
            break

    return repositories


@temple.utils.set_cmd_env_var('ls')
def ls(github_user, template=None):
    """Lists all temple templates and packages associated with those templates

    If ``template`` is None, returns the available templates for the configured
    Github org.

    If ``template`` is a Github path to a template, returns all projects spun
    up with that template.

    ``ls`` uses the github search API to find results.

    Note that the `temple.constants.TEMPLE_ENV_VAR` is set to 'ls' for the duration of this
    function.

    Args:
        github_user (str): The github user or org being searched.
        template (str, optional): The template git repo path. If provided, lists
            all projects that have been created with the provided template. Note
            that the template path is the SSH path
            (e.g. git@github.com:CloverHealth/temple.git)

    Returns:
        dict: A dictionary of repository information keyed on the SSH Github url

    Raises:
        `InvalidGithubUserError`: When ``github_user`` is invalid
    """
    temple.check.has_env_vars(temple.constants.GITHUB_API_TOKEN_ENV_VAR)

    if template:
        temple.check.is_git_ssh_path(template)
        search_q = 'user:{} filename:{} {}'.format(
            github_user,
            temple.constants.TEMPLE_CONFIG_FILE,
            template)
    else:
        search_q = 'user:{} cookiecutter.json in:path'.format(github_user)

    results = _code_search(search_q, github_user)
    return collections.OrderedDict(sorted(results.items()))
