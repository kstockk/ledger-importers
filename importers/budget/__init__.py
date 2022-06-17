from xml.sax.handler import LexicalHandler
from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import amount
from beancount.core import flags
from beancount.core import data

from datetime import date
from dateutil.parser import parse

from decimal import Decimal
import csv
import os
import re
import collections

# Credits to https://gist.github.com/mterwill/7fdcc573dc1aa158648aacd4e33786e8#file-importers-chase-py

class CSVImporter(importer.ImporterProtocol):
    def identify(self, f):
        return re.match("b_.*\.csv", os.path.basename(f.name))

    def extract(self, f):
        entries = []

        account_map = CSVImporter.get_account_map()

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                # Assign variables
                account = row["Account"]
                trans_date = parse(row["Date"]).date()
                payee = row["Payee"]
                desc = row["Notes"]
                category = row["Category"]
                amnt = row["Amount"]

                # Search and replace account and category according to the account map
                for ledger, budget in account_map.items():
                    if account == budget and account != "":
                        account = ledger
                    if category == budget and category != "":
                        category = ledger

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_OKAY,
                    payee=payee if category != "" else "Transfer",
                    narration=desc if category != "" else payee,
                    tags=set(),
                    links=set(),
                    postings=[],
                )
                
                txn.postings.append(
                    data.Posting(account, amount.Amount(D(amnt),
                        "AUD"), None, None, None, None)
                )

                if category != "":
                    txn.postings.append(
                        data.Posting(category, amount.Amount(D(amnt)*-1,
                            "AUD"), None, None, None, None)
                    )

                entries.append(txn)

        return entries

    @staticmethod
    def get_account_map():
        with open("/bean/data/account_map.csv") as f:
            reader = csv.reader(f)
            account_map = {rows[0]:rows[1] for rows in reader}
            return account_map
                