# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass

from dazl import exercise, create_and_exercise
from dazl.model.core import ContractData

from daml_dit_if.api import \
    IntegrationEnvironment, IntegrationEvents


LOG = logging.getLogger('integration')


@dataclass
class IntegrationLoopbackEnv(IntegrationEnvironment):
    templateFilter: str
    targetContractMode: str
    targetTemplate: str
    templateChoice: str
    keyField: str


def integration_loopback_main(
        env: 'IntegrationLoopbackEnv',
        events: 'IntegrationEvents'):

    @events.ledger.contract_created(env.templateFilter)
    async def on_contract_created(event):

        LOG.info('loopback - created: %r (%r)', event, env.targetContractMode)

        if env.targetContractMode == 'Trigger Contract':
            return [exercise(event.cid, env.templateChoice, {})]

        elif env.targetContractMode == 'Create and Exercise':
            return [create_and_exercise(
                env.targetTemplate,
                {'integrationParty': env.party},
                env.templateChoice,
                {'cid': event.cid})]

        elif env.targetContractMode == 'Exercise by Key':

            cdata = event.cdata

            try:
                key_value = cdata[env.keyField]
            except:
                raise Exception(
                    f'Missing key field {event.keyField} in triggering'
                    f' contract {cdata}.')

            return [create_and_exercise(
                env.targetTemplate,
                {'integrationParty': env.party},
                env.templateChoice,
                {'cid': event.cid})]
