
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

CSV_HEADER = "Id,Wallet,Transaction Date,Type,Subtype,Asset,Amount,Costbase,Remarks,Txid,Realised.TAX_GAIN"

class CryptoImporter(importer.ImporterProtocol):
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
            txid = row["Txid"]
            wallet = row["Wallet"]
            parsed_date = datetime.strptime(row["Transaction Date"], '%d/%m/%Y').date()
            txtype = row["Type"]
            subtype = row["Subtype"]
            asset = row["Asset"].split("#")[0]
            ledger_asset = "Assets:Crypto:" + asset
            amnt = D(row["Amount"])
            cost = D(row["Costbase"])
            cost = cost if amnt > 0 else cost * -1
            price = cost / amnt
            tax_gain = D(row["Realised.TAX_GAIN"])
            remarks = row["Remarks"]

            meta = data.new_metadata(f.name, index, {"txid": txid})

            narrate = " - ".join([wallet, txtype, subtype, remarks])

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


            if amnt > 0:
                txn.postings.insert(0, data.Posting(
                    ledger_asset,
                    amount.Amount(amnt, asset),
                    Cost(price, 'AUD', None, None),
                    None,
                    None,
                    None
                )
                )
                ledger_account = "Assets:Crypto:Cash" if txtype == "Buy" else "Income:Crypto:Market-Movement"
                if txtype != "Earn":
                    txn.postings.insert(0, data.Posting(
                        ledger_account,
                        amount.Amount(-cost, 'AUD'),
                        None,
                        None,
                        None,
                        None
                    )
                    )
            if amnt < 0:
                txn.postings.insert(0, data.Posting(
                    ledger_asset,
                    amount.Amount(amnt, asset),
                    Cost(None, 'AUD', None, None),
                    amount.Amount(price, 'AUD'),
                    None,
                    None
                )
                )
                if txtype == "Sell":
                    ledger_account = "Assets:Crypto:Cash"
                else:
                    ledger_account = "Income:Crypto:Market-Movement"
                txn.postings.insert(0, data.Posting(
                    ledger_account,
                    amount.Amount(-cost, 'AUD'),
                    None,
                    None,
                    None,
                    None
                )
                )
                txn.postings.insert(1, data.Posting(
                    "Income:Crypto:Gains",
                    amount.Amount(tax_gain * -1, 'AUD'),
                    None,
                    None,
                    None,
                    None
                    )
                    )
            if txtype == "Earn":
                txn.postings.insert(1, data.Posting(
                    "Income:Crypto:Income",
                    amount.Amount(cost * -1, 'AUD'),
                    None,
                    None,
                    None,
                    None
                    )
                    )
            entries.append(txn)
        return entries
