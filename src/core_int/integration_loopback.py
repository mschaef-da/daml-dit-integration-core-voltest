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


def integration_loopback_main(
        env: 'IntegrationLoopbackEnv',
        events: 'IntegrationEvents'):

    @events.ledger.contract_created(env.templateFilter)
    async def on_contract_created(event):

        LOG.info('loopback - created: %r (%r)', event, env.targetContractMode)

        if env.targetContractMode == 'Trigger Contract':
            return [exercise(event.cid, env.templateChoice, {})]
        else:
            return [create_and_exercise(
                env.targetTemplate,
                {'integrationParty': env.party},
                env.templateChoice,
                {'cid': event.cid})]
