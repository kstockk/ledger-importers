
from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import amount
from beancount.core.position import Cost
from beancount.core import flags
from beancount.core import data

import csv
import os
import re
from datetime import datetime
from itertools import chain, groupby
from operator import itemgetter

CSV_HEADER = "Date,Type,Description,Unit price,Units,Amount"

class IoofImporter(importer.ImporterProtocol):
    def __init__(self, file_encoding='utf-8-sig'):
        self.file_encoding = file_encoding

    def identify(self, file_):
        with open(file_.name, encoding=self.file_encoding) as f:
            header = f.readline().strip().split(',')
            csv_header = CSV_HEADER.strip().split(',')
        return header == csv_header

    def extract(self, file_):
        # Store csv rows in dict
        with open(file_.name, mode='r', encoding=self.file_encoding) as f:
            rows = [row for row in csv.DictReader(f)]

        entries = []
        for index, row in enumerate(rows):
            parsed_date = datetime.strptime(row["Date"], '%d/%m/%Y').date()
            txtype = row["Type"]
            desc = row["Description"]
            price = D(row["Unit price"])
            units = D(row["Units"])
            amnt = D(row["Amount"])

            meta = data.new_metadata(f.name, index)

            narrate = " - ".join([txtype, desc])

            txn = data.Transaction(
                meta=meta,
                date=parsed_date,
                flag=flags.FLAG_OKAY,
                payee="",
                narration=narrate,
                tags=set(),
                links=set(),
                postings=[],
            )

            if desc == "IOOF MultiMix Growth Trust":
                asset = "IOF0097AU"

            if txtype == "Buys":
                txn.postings.insert(0, data.Posting(
                    "Assets:Super:IOOF-Employer-Super:" + asset,
                    amount.Amount(units, asset),
                    Cost(price, 'AUD', None, None),
                    None,
                    None,
                    None
                )),
                txn.postings.insert(1, data.Posting(
                    "Assets:Super:IOOF-Employer-Super:Cash",
                    amount.Amount(amnt, 'AUD'),
                    None,
                    None,
                    None,
                    None
                ))

            if txtype == "Deposit":
                txn.postings.insert(0, data.Posting(
                    "Assets:Super:IOOF-Employer-Super:Cash",
                    amount.Amount(amnt, 'AUD'),
                    None,
                    None,
                    None,
                    None
                )),
                txn.postings.insert(1, data.Posting(
                    "Income:Super:Income",
                    amount.Amount(-amnt, 'AUD'),
                    None,
                    None,
                    None,
                    None
                ))

            if txtype == "Sells":
                txn.postings.insert(0, data.Posting(
                    "Assets:Super:IOOF-Employer-Super:" + asset,
                    amount.Amount(units, asset),
                    Cost(price, 'AUD', None, None),
                    None,
                    None,
                    None
                )),
                txn.postings.insert(1, data.Posting(
                    "Assets:Super:IOOF-Employer-Super:Cash",
                    amount.Amount(amnt, 'AUD'),
                    None,
                    None,
                    None,
                    None
                ))

            #     ledger_account = "Assets:Crypto:Cash" if txtype == "Buy" else "Income:Crypto:Market-Movement"
            #     if txtype != "Earn":
            #         txn.postings.insert(0, data.Posting(
            #             ledger_account,
            #             amount.Amount(-cost, 'AUD'),
            #             None,
            #             None,
            #             None,
            #             None
            #         )
            #         )
            # if amnt < 0:
            #     txn.postings.insert(0, data.Posting(
            #         ledger_asset,
            #         amount.Amount(amnt, asset),
            #         Cost(None, 'AUD', None, None),
            #         amount.Amount(price, 'AUD'),
            #         None,
            #         None
            #     )
            #     )
            #     if txtype == "Sell":
            #         ledger_account = "Assets:Crypto:Cash"
            #     else:
            #         ledger_account = "Income:Crypto:Market-Movement"
            #     txn.postings.insert(0, data.Posting(
            #         ledger_account,
            #         amount.Amount(-cost, 'AUD'),
            #         None,
            #         None,
            #         None,
            #         None
            #     )
            #     )
            #     txn.postings.insert(1, data.Posting(
            #         "Income:Crypto:Gains",
            #         amount.Amount(tax_gain * -1, 'AUD'),
            #         None,
            #         None,
            #         None,
            #         None
            #         )
            #         )
            entries.append(txn)
        return entries
