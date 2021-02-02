# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from dataclasses import dataclass

from dazl import exercise

from daml_dit_if.api import \
    IntegrationEnvironment, IntegrationEvents


LOG = logging.getLogger('integration')


@dataclass
class IntegrationTimerEnv(IntegrationEnvironment):
    interval: int
    targetTemplate: str
    templateChoice: str


def integration_timer_main(
        env: 'IntegrationEnvironment',
        events: 'IntegrationEvents'):

    active_cids = set()

    @events.ledger.contract_created(env.targetTemplate)
    async def on_contract_created(event):
        LOG.debug('Created CID: %r', event.cid)
        active_cids.add(event.cid)

    @events.ledger.contract_archived(env.targetTemplate)
    async def on_ledger_archived(event):
        LOG.debug('Archived CID: %r', event.cid)
        active_cids.discard(event.cid)

    @events.time.periodic_interval(env.interval)
    async def interval_timer_elapsed():
        LOG.debug('Timer elapsed: %r', active_cids)
        return [exercise(cid, env.templateChoice, {})
                for cid
                in active_cids]
