# Copyright (c) 2020, Digital Asset (Switzerland) GmbH and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from dataclasses import dataclass
from datetime import datetime

from dazl import exercise

from daml_dit_if.api import \
    IntegrationEnvironment, IntegrationEvents, IntegrationWebhookResponse

from daml_dit_if.main.web import json_response

LOG = logging.getLogger('integration')


@dataclass
class IntegrationLedgerEventLogEnv(IntegrationEnvironment):
    historyBound: int


def integration_ledger_event_log_main(
        env: 'IntegrationEnvironment',
        events: 'IntegrationEvents'):

    history = []

    def extend_history(event_data):
        nonlocal history
        history.append(event_data)

        if env.historyBound > 0:
            history = history[-env.historyBound:]

    def _event_description(type):
        return {
            'type': type,
            'integration_time': datetime.utcnow()
        }

    @events.ledger.ledger_init()
    async def on_ledger_init():
        LOG.info('ledger_init')
        extend_history(_event_description('ledger_init'))

    @events.ledger.ledger_ready()
    async def on_ledger_ready():
        LOG.info('ledger_ready')
        extend_history(_event_description('ledger_ready'))

    @events.ledger.transaction_start()
    async def on_transaction_start(event):
        LOG.info('transaction_start: %r', event)

        extend_history({
            **_event_description('transaction_start'),
            'command_id': event.command_id,
            'workflow_id': event.workflow_id
        })

    @events.ledger.transaction_end()
    async def on_transaction_end(event):
        LOG.info('transaction_end: %r', event)

        extend_history({
            **_event_description('transaction_end'),
            'command_id': event.command_id,
            'workflow_id': event.workflow_id
        })

    @events.ledger.contract_created('*', flow=False)
    async def on_contract_sweep(event):
        LOG.info('contract_created (sweep): %r', event)

    @events.ledger.contract_created('*', sweep=False)
    async def on_contract_created(event):
        LOG.info('contract_created: %r', event)

        extend_history({
            **_event_description('contract_created'),
            'cid': str(event.cid),
            'cdata': event.cdata
        })

    @events.ledger.contract_archived('*')
    async def on_contract_archived(event):
        LOG.info('contract_archived: %r', event)

        extend_history({
            **_event_description('contract_archived'),
            'cid': str(event.cid)
        })

    @events.webhook.get(label='Transactions')
    async def on_get_transactions(request):
        return IntegrationWebhookResponse(
            response=json_response({'transactions': history}))

    @events.webhook.post(url_suffix='/reset', label='Reset')
    async def on_reset(request):
        nonlocal history
        history = []
        return IntegrationWebhookResponse()
