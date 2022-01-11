"""
Utilities for accessing and traversing different git forges, along with pulling down
remote templates.

Currently Github and Gitlab are supported
"""
import abc
import collections
import os
import re
import subprocess
from urllib.parse import urlparse

import gitlab
import gitlab.const
import requests
import tldextract

import temple.check


def from_path(path):
    """
    Given a forge path, such as Github or Gitlab, return a client for accessing
    the repository information.

    Args:
        path (str): A path under which templates are stored.
            For example, a Github organization or user (e.g. github.com/Organization)
            or a Gitlab group (e.g. gitlab.com/my/group).
    """
    if "github.com" in path:
        return Github()
    elif "gitlab.com" in path:
        return Gitlab()
    else:
        raise temple.exceptions.InvalidRootError(
            "Invalid forge provided. Must provide either a Github user/organization"
            " (e.g. github.com/UserName) or"
            " a Gitlab group (e.g. gitlab.com/my/group).",
        )


def get_name_from_ssh_path(template_path):
    matches = re.search(r"\/([^/]+)\.git$", template_path)
    return matches.group(1)


def _get_latest_template_version_w_ssh(template):
    """
    Tries to obtain the latest template version using an SSH key
    """
    cmd = "git ls-remote {} | grep HEAD | cut -f1".format(template)
    ret = temple.utils.shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = ret.stderr.decode("utf-8").strip()
    stdout = ret.stdout.decode("utf-8").strip()
    if stderr and not stdout:
        raise RuntimeError(
            ('An unexpected error happened when running "{}". (stderr="{}"').format(
                cmd, stderr
            )
        )
    return stdout


class Forge(metaclass=abc.ABCMeta):
    """The base class for all git forges.

    Forges must implement both ``ls`` for listing templates/projects
    and ``_get_latest_template_version`` for finding the latest version
    of a template. The ``api_token_env_var_name`` property must also
    be configured.
    """

    @abc.abstractmethod
    def ls(self, path, template=None):
        """Implements ls for the forge"""
        pass

    @property
    @abc.abstractmethod
    def api_token_env_var_name(self):
        """Returns the environment variable name for configuring an API token"""
        pass

    def get_latest_template_version(self, template):
        """Retrieves the latest template SHA

        Returns:
            str: The latest template version
        """
        try:
            latest_version = _get_latest_template_version_w_ssh(template)
        except (subprocess.CalledProcessError, RuntimeError):
            try:
                latest_version = self._get_latest_template_version(template)
            except (
                requests.exceptions.RequestException,
                temple.exceptions.InvalidEnvironmentError,
            ) as exc:
                raise temple.exceptions.CheckRunError(
                    (
                        'Could not obtain the latest template version of "{}"'
                        " using git SSH key or the configured {} API token."
                        ' Set either a "{}" environment variable'
                        " with access to the template or obtain permission so that"
                        " the git SSH key can access it."
                    ).format(
                        template,
                        self.__class__.__name__,
                        self.api_token_env_var_name,
                    )
                ) from exc

        return latest_version

    @abc.abstractmethod
    def _get_latest_template_version(self, template):
        """Finds the latest version of a template using an API

        By default, the latest version of a template is used with standard
        git calls and SSH auth. However, one must implement this method
        as a fallback in case only API access is available.
        """
        pass


class Github(Forge):
    """A Github forge"""

    @property
    def api_token_env_var_name(self):
        return temple.constants.GITHUB_API_TOKEN_ENV_VAR

    def _call_api(self, verb, url, **request_kwargs):
        """Perform a github API call

        Args:
            verb (str): Can be "post", "put", or "get"
            url (str): The base URL with a leading slash for Github API (v3)
            auth (str or HTTPBasicAuth): A Github API token or a HTTPBasicAuth object
        """
        temple.check.has_env_vars(temple.constants.GITHUB_API_TOKEN_ENV_VAR)
        api_token = os.environ[temple.constants.GITHUB_API_TOKEN_ENV_VAR]
        api = "https://api.github.com{}".format(url)
        auth_headers = {"Authorization": "token {}".format(api_token)}
        headers = {**auth_headers, **request_kwargs.pop("headers", {})}
        return getattr(requests, verb)(api, headers=headers, **request_kwargs)

    def _get(self, url, **request_kwargs):
        """Github API get"""
        return self._call_api("get", url, **request_kwargs)

    def _parse_link_header(self, headers):
        """A utility function that parses Github's link header for pagination."""
        links = {}
        if "link" in headers:
            link_headers = headers["link"].split(", ")
            for link_header in link_headers:
                (url, rel) = link_header.split("; ")
                url = url[1:-1]
                rel = rel[5:-1]
                links[rel] = url
        return links

    def _code_search(self, query, forge=None):
        """Performs a Github API code search

        Args:
            query (str): The query sent to Github's code search
            root (str, optional): The root being searched in Github

        Returns:
            dict: A dictionary of repository information keyed on the git SSH url

        Raises:
            `InvalidRootError`: When ``root`` is invalid
        """
        headers = {"Accept": "application/vnd.github.v3.text-match+json"}

        resp = self._get(
            "/search/code", params={"q": query, "per_page": 100}, headers=headers
        )

        if resp.status_code == requests.codes.unprocessable_entity and forge:
            raise temple.exceptions.InvalidRootError(
                'Invalid Github forge - "{}"'.format(forge)
            )
        resp.raise_for_status()

        resp_data = resp.json()

        repositories = collections.defaultdict(dict)
        while True:
            repositories.update(
                {
                    "git@github.com:{}.git".format(
                        repo["repository"]["full_name"]
                    ): repo["repository"]
                    for repo in resp_data["items"]
                }
            )

            next_url = self._parse_link_header(resp.headers).get("next")
            if next_url:
                resp = requests.get(next_url, headers=headers)
                resp.raise_for_status()
                resp_data = resp.json()
            else:
                break

        return repositories

    def _get_latest_template_version(self, template):
        """Tries to obtain the latest template version with the Github API"""
        repo_path = temple.utils.get_repo_path(template)
        api = "/repos/{}/commits".format(repo_path)

        last_commit_resp = self._get(api, params={"per_page": 1})
        last_commit_resp.raise_for_status()

        content = last_commit_resp.json()
        assert len(content) == 1, "Unexpected Github API response"
        return content[0]["sha"]

    def ls(self, path, template=None):
        """Return a list of repositories under the forge path or the template (if provided)."""

        path_parts = path.strip().split("/")
        if path_parts[-1] == "":
            user_or_org = path_parts[-2]
        else:
            user_or_org = path_parts[-1]

        if template:
            temple.check.is_git_ssh_path(template)
            template_repo_name = get_name_from_ssh_path(template)

            search_q = "user:{} filename:{} {}".format(
                user_or_org, temple.constants.TEMPLE_CONFIG_FILE, template_repo_name
            )
        else:
            search_q = "user:{} filename:cookiecutter.json".format(user_or_org)

        results = self._code_search(search_q, forge=path)
        return collections.OrderedDict(
            sorted(
                [
                    (key, value["description"] or "(no description found)")
                    for key, value in results.items()
                ]
            )
        )


class Gitlab(Forge):
    """A Gitlab forge"""

    @property
    def api_token_env_var_name(self):
        return temple.constants.GITLAB_API_TOKEN_ENV_VAR

    def get_client(self, gitlab_url):
        temple.check.has_env_vars(self.api_token_env_var_name)
        api_token = os.environ[self.api_token_env_var_name]
        return gitlab.Gitlab(url=gitlab_url, private_token=api_token)

    def _get_gitlab_url_and_repo_path(self, template):
        """Given a template, return a gitlab url and a repo path"""
        repo_path = temple.utils.get_repo_path(template)

        # Figure out the top-level gitlab domain. Note that it's assumed
        # the template is an SSH path in the format of git@domain:path
        domain = template.split(":")[0].split("@")[1]
        gitlab_url = "https://" + domain

        return gitlab_url, repo_path

    def _get_latest_template_version(self, template):  # pragma: no cover
        """Tries to obtain the latest template version with the Gitlab API"""
        gitlab_url, repo_path = self._get_gitlab_url_and_repo_path(template)

        gl = self.get_client(gitlab_url)
        project = gl.projects.get(repo_path)
        sha = project.commits.list()[0].id

        return sha

    def _get_gitlab_url_and_group(self, forge):
        """Given a forge, return a gitlab url and group"""
        if not forge.startswith("http"):
            forge = "https://" + forge

        url_parts = urlparse(forge)
        gitlab_url = url_parts.scheme + "://" + url_parts.netloc
        group = url_parts.path.strip("/")

        # If users are listing templates on gitlab.com and not a self-hosted gitlab,
        # do not allow them to query the root gitlab.com
        is_self_hosted = tldextract.extract(forge).domain != "gitlab"

        if not group and not is_self_hosted:
            raise temple.exceptions.InvalidGitlabGroupError(
                "Must provide a gitlab group, for example gitlab.com/group"
            )

        return gitlab_url, group

    def ls(self, forge, template=None):  # pragma: no cover
        """Return a list of repositories under the forge path or the template (if provided)."""
        gitlab_url, group = self._get_gitlab_url_and_group(forge)

        gl = self.get_client(gitlab_url)
        if group:
            # Search under a group if one is specified
            gl = gl.groups.get(group)

        # Search for either templates (with cookiecutter.json) or projects that have been made
        # from the template. Note - advanced search must be turned on for the Gitlab instance
        if not template:
            results = gl.search(
                gitlab.const.SEARCH_SCOPE_BLOBS, search="filename:cookiecutter.json"
            )
        else:
            results = gl.search(
                gitlab.const.SEARCH_SCOPE_BLOBS,
                search="{} filename:temple.yaml".format(template),
            )

        # Fetch projects associated with search results
        gl = self.get_client(gitlab_url)
        projects = [gl.projects.get(r["project_id"]) for r in results]

        return collections.OrderedDict(
            sorted(
                [
                    (p.ssh_url_to_repo, p.description or "(no description found)")
                    for p in projects
                ]
            )
        )
