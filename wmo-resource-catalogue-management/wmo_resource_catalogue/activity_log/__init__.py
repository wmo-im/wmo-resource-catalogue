###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

from datetime import datetime, timezone
import logging
from pathlib import Path

import click

from pywis_pubsub import cli_options

from wmo_resource_catalogue.backend import BACKENDS
from wmo_resource_catalogue.env import BACKEND_TYPE, BACKEND_CONNECTION

LOGGER = logging.getLogger(__name__)

BACKEND_DEFS = {
    'connection': BACKEND_CONNECTION,
    'collection': 'wmo-resource-catalogue-activity-log',
    'settings_file': Path(__file__).resolve().parent.parent / 'resources' / 'activity-log' / 'es-settings.json'  # noqa
}


class ActivityLog:
    def __init__(self):
        """
        Initializer

        :returns: `wmo_resource_catalogue.activity_log.ActivityLog`
        """

        self.backend = BACKENDS[BACKEND_TYPE](BACKEND_DEFS)

    def publish(self, message: dict):
        """
        Publish activity log entry to backend

        :param message: `dict` of job message

        :returns: `None`
        """

        LOGGER.info(f'Saving to {BACKEND_TYPE} ({BACKEND_DEFS})')

        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        job_id = message['id']

        job = {
            'id': job_id,
            'identifier': job_id,
            'type': 'process',
            'process_id': None,
            'progress': 100,
            'created': now,
            'started': now,
            'finished': now,
            'updated': None,
            'status': 'successful',
            'message': message,
            'mimetype': 'application/json'
        }

        self.backend.save_record(job)


@click.command()
@click.pass_context
@click.option('--force', '-f', 'force', is_flag=True, default=False,
              help='Force reinitialization of backend')
@click.option('--yes', '-y', 'bypass', is_flag=True, default=False,
              help='Bypass permission prompts')
@cli_options.OPTION_VERBOSITY
def setup(ctx, force, bypass, verbosity='NOTSET'):
    """Create Activity Log backend"""

    backend = BACKENDS[BACKEND_TYPE](BACKEND_DEFS)
    LOGGER.debug(f'Backend: {backend}')

    if backend.exists():
        if not force:
            click.echo('Backend already exists')
            return
        else:
            if bypass:
                click.echo('Reinitializing backend')
                backend.teardown()
                backend.setup()
            else:
                msg = ('Recreate backend?  This will delete all job metadata '
                       'and delete/setup/reinitialize the backend.')

                if not click.confirm(msg, abort=True):
                    click.echo('Not reinitializing backend')
                    return
                else:
                    click.echo('Reinitializing backend')
                    backend.teardown()
                    backend.setup()
    else:
        click.echo('Setting up backend')
        backend.setup()

    click.echo('Done')


@click.command()
@click.pass_context
@click.option('--yes', '-y', 'bypass', is_flag=True, default=False,
              help='Bypass permission prompts')
@cli_options.OPTION_VERBOSITY
def teardown(ctx, bypass, verbosity='NOTSET'):
    """Delete Activity Log backend"""

    msg = 'Delete Activity Log backend?  This will remove all existing job metadata'  # noqa
    if not bypass:
        if not click.confirm(msg, abort=True):
            return

    backend = BACKENDS[BACKEND_TYPE](BACKEND_DEFS)
    LOGGER.debug(f'Backend: {backend}')
    backend.teardown()

    click.echo('Done')


@click.group()
def activity_log():
    """Activity Log utilities"""

    pass


activity_log.add_command(setup)
activity_log.add_command(teardown)
