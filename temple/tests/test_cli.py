"""Tests for temple.cli module"""
# pylint: disable=no-value-for-parameter
import collections
import sys

import click
import pytest

import temple.cli
import temple.exceptions


@pytest.fixture
def mock_exit(mocker):
    yield mocker.patch('sys.exit', autospec=True)


@pytest.fixture
def mock_successful_exit(mock_exit):
    yield
    mock_exit.assert_called_once_with(0)


@pytest.mark.usefixtures('mock_successful_exit')
@pytest.mark.parametrize('subcommand, args, expected_function, exp_call_args, exp_call_kwargs', [
    ('setup', ['t'], 'temple.setup.setup', ['t'], {'version': None}),
    ('setup', ['t', '-v', 'v1'], 'temple.setup.setup', ['t'], {'version': 'v1'}),
    ('update', [], 'temple.update.update', [], {'new_version': None, 'enter_parameters': False}),
    ('update', ['-c', '-v', 'v1'], 'temple.update.up_to_date', [], {'version': 'v1'}),
    ('ls', ['user'], 'temple.ls.ls', ['user'], {'template': None}),
    ('ls', ['user', 'template'], 'temple.ls.ls', ['user'], {'template': 'template'}),
    ('clean', [], 'temple.clean.clean', [], {}),
    ('switch', ['new_t', '-v', 'new_v'], 'temple.update.update', [],
     {'new_template': 'new_t', 'new_version': 'new_v'}),
])
def test_main(subcommand, args, expected_function, exp_call_args, exp_call_kwargs, mocker):
    """Verify calling the CLI subcommands works as expected"""
    mocker.patch.object(sys, 'argv', ['temple', subcommand] + args)
    mock_expected_func = mocker.patch(expected_function, autospec=True)

    temple.cli.main()

    mock_expected_func.assert_called_once_with(*exp_call_args, **exp_call_kwargs)


@pytest.mark.usefixtures('mock_successful_exit')
def test_main_w_version(mocker, capsys):
    """Test calling the CLI with the --version option"""
    mocker.patch.object(sys, 'argv', ['temple', '--version'])

    temple.cli.main()

    out, _ = capsys.readouterr()
    assert out == 'temple %s\n' % temple.__version__


@pytest.mark.usefixtures('mock_successful_exit')
def test_main_no_args(mocker, capsys):
    """Test calling the CLI with no options"""
    mocker.patch.object(sys, 'argv', ['temple'])
    mocker.patch.object(click.Context, 'get_help', autospec=True, return_value='help_text')

    temple.cli.main()

    out, _ = capsys.readouterr()
    assert out == 'help_text\n'


@pytest.mark.usefixtures('mock_exit')
@pytest.mark.parametrize('version, up_to_date_return', [
    pytest.mark.xfail((None, False), raises=temple.exceptions.NotUpToDateWithTemplateError),
    (None, True),
    ('version', True),
])
def test_update_check(version, up_to_date_return, capsys, mocker):
    """Verifies checking for updates when calling temple update -c"""
    mocker.patch.object(sys, 'argv', ['temple', 'update', '-c', '-v', version])
    mock_up_to_date = mocker.patch('temple.update.up_to_date', autospec=True,
                                   return_value=up_to_date_return)

    temple.cli.main()

    out, _ = capsys.readouterr()
    assert out == 'Temple package is up to date\n'
    mock_up_to_date.assert_called_once_with(version=version)


@pytest.mark.usefixtures('mock_successful_exit')
@pytest.mark.parametrize('ls_args, expected_out', [
    (['temple', 'ls', 'user'], 'ls\nvalues\n'),
    (['temple', 'ls', 'user', '-l'], 'ls - ls descr\nvalues - (no project description found)\n'),
])
def test_ls(ls_args, expected_out, capsys, mocker):
    """Verify ls prints results properly"""
    mocker.patch('temple.ls.ls', autospec=True, return_value=collections.OrderedDict([
        ('ls', {'description': 'ls descr'}),
        ('values', {'description': ''}),
    ]))
    mocker.patch.object(sys, 'argv', ls_args)

    temple.cli.main()

    out, _ = capsys.readouterr()
    assert out == expected_out
