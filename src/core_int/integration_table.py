
# SPDX-License-Identifier: Apache-2.0

import asyncio
import csv
import operator
from functools import reduce
from decimal import Decimal

from io import StringIO

from dataclasses import dataclass

from dazl import exercise

from datetime import date, datetime, timezone

from daml_dit_if.api import \
    IntegrationEnvironment, \
    IntegrationEvents, \
    IntegrationWebhookResponse, \
    getIntegrationLogger, \
    empty_success_response, \
    blob_success_response

from daml_dit_if.main.web import json_response

LOG = getIntegrationLogger()


def datetimestr(dt):
    return dt.strftime("%d/%m/%Y %H:%M:%S %Z")

def datestr(dt):
    return dt.strftime("%d/%m/%Y")

def getin(o, path):
    if not len(path):
        return o
    elif o is None or type(o) != dict:
        return 0
    else:
        return getin(o.get(path[0], None), path[1:])

def flatone(l):
    return reduce(operator.add, l, [])

def fieldkeys(o, path=[]):
    if o is None or type(o) != dict:
        return [path]
    else:
        return flatone([fieldkeys(o.get(k), [*path, k]) for k in o.keys()])

def fieldkeyname(key):
    return "_".join(key)

@dataclass
class IntegrationTableEnv(IntegrationEnvironment):
    targetTemplate: str
    csvDialect: str

CSV_DIALECTS = {
    "Excel": "excel",
    "Excel w/Tabs": "excel-tab",
    "Unix": "unix"
}

def integration_table_main(
        env: 'IntegrationTableEnv',
        events: 'IntegrationEvents'):

    active_contracts = {}

    @events.ledger.contract_created(env.targetTemplate)
    async def on_contract_created(event):
        LOG.debug('Created CID: %r', event.cid)
        active_contracts[event.cid] = event.cdata

    @events.ledger.contract_archived(env.targetTemplate)
    async def on_ledger_archived(event):
        LOG.debug('Archived CID: %r', event.cid)
        active_contracts.pop(event.cid, None)

    def contract_value_column(val):
        t = type(val)

        if t in [int, float, str, Decimal]:
            return str(val)
        elif t == date:
            return datestr(val)
        elif t == datetime:
            return datetimestr(val)
        else:
            return None

    def find_contract_scalar_columns(cdata):
        return [key
                for key
                in fieldkeys(cdata)
                if contract_value_column(getin(cdata, key)) is not None]

    def get_formatted_table_data():
        LOG.info('Generating Table: %r', active_contracts)

        if len(active_contracts) == 0:
            return []

        first_row = active_contracts[next(iter(active_contracts))]

        LOG.debug('first_row: %r', first_row)

        contract_columns = find_contract_scalar_columns(first_row)

        LOG.debug('contract_columns: %r', contract_columns)

        fieldnames = [fieldkeyname(col) for col in contract_columns]

        LOG.debug('fieldnames: %r', fieldnames)

        row_maps = [{fieldkeyname(key) : contract_value_column(getin(cdata, key))
                     for key
                     in contract_columns}
                    for cid, cdata
                    in active_contracts.items()]

        LOG.debug('row_maps: %r', row_maps)

        return row_maps

    @events.webhook.get(label='CSV Table')
    async def on_get_table_csv(request):
        row_data = get_formatted_table_data()

        if len(row_data):
            file = StringIO()
            csvout = csv.DictWriter(file, fieldnames=list(row_data[0].keys()), dialect=CSV_DIALECTS[env.csvDialect])

            csvout.writeheader()
            for row in row_data:
                csvout.writerow(row)

            report_text = file.getvalue()
        else:
            report_text = 'no data'

        return IntegrationWebhookResponse(
            response=blob_success_response(report_text, "text/csv"))

    @events.webhook.get(url_suffix='/json', label='JSON Table')
    async def on_get_table_json(request):
        row_data = get_formatted_table_data()

        return IntegrationWebhookResponse(
            response=json_response({'rows': row_data}))

