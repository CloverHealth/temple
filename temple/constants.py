"""
temple.constants
~~~~~~~~~~~~~~~~

Constants for temple
"""

#: The environment variable set when running any temple command. It is set to
#: the name of the command
TEMPLE_ENV_VAR = '_TEMPLE'

#: The temple config file in each repo
TEMPLE_CONFIG_FILE = 'temple.yaml'

#: The Github API token environment variable
GITHUB_API_TOKEN_ENV_VAR = 'GITHUB_API_TOKEN'

#: Temple docs URL
TEMPLE_DOCS_URL = 'https://github.com/CloverHealth/temple'

#: The temporary branches used for updates
UPDATE_BRANCH_NAME = '_temple_update'
TEMP_UPDATE_BRANCH_NAME = UPDATE_BRANCH_NAME + '_temp'
