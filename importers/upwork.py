
import csv
import os
from dateutil.parser import parse

import beangulp

from beancount.core.number import D
from beancount.core import amount
from beancount.core import flags
from beancount.core import data

CSV_HEADER = [
    "Date",
    "Transaction ID",
    "Transaction Type",
    "Transaction Summary",
    "Transaction Summary Details",
    "Description 1",
    "Description 2",
    "Description 3",
    "Entered Description",
    "Agency",
    "Freelancer",
    "Team",
    "Account Name",
    "PO",
    "Ref ID",
    "Amount $",
    "Amount in local currency",
    "Currency",
    "Current Balance $",
    "Payment Method",
]

desc_fields = [
    "Transaction Summary",
    "Transaction Summary Details"
]

ACCOUNT_MAPPING = {
    "Fixed-price": "Income:Freelance:Upwork:Fixed-Priced",
    "Hourly": "Income:Freelance:Upwork:Hourly",
    "Bonus": "Income:Freelance:Upwork:Bonus",
    "GST": "Expenses:Freelance:Upwork:GST",
    "Connects": "Expenses:Freelance:Upwork",
    "Subscription": "Expenses:Freelance:Upwork",
    "Service Fee": "Expenses:Freelance:Upwork:Service-Fees",
    "Payment": "Liabilities:Suspense",
}

# def parse_date(text):
#     for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%B %d, %Y', '%b %d, %Y'):
#         try:
#             return datetime.strptime(text, fmt).date()
#         except ValueError:
#             pass
#     raise ValueError('no valid date format found')

def concat_fields(row: dict, sep=" | ") -> str:
    return sep.join(
        str(row.get(key, "")).strip()
        for key in desc_fields
        if row.get(key) not in (None, "")
    )

def get_map(key):
    return ACCOUNT_MAPPING.get(key, key)

class Importer(beangulp.Importer):
    def __init__(self, account, currency, file_encoding='utf-8-sig'):
        self.importer_account = account
        self.file_encoding = file_encoding
        self.currency = currency

    def identify(self, filepath):
        with open(filepath, encoding=self.file_encoding) as f:
            header = f.readline().strip().split(',')
        return header == CSV_HEADER

    def account(self, filepath):
        return self.importer_account

    def extract(self, filepath, existing):
        entries = []

        with open(filepath, mode='r', encoding=self.file_encoding) as f:
            for index, row in enumerate(csv.DictReader(f)):
                parsed_date = parse(row["Date"]).date()
                trans_type = row["Team"] or "Upwork"
                account_cash = self.importer_account
                account_pnl = get_map(row["Transaction Type"])
                desc = concat_fields(row)
                amnt = row["Amount $"]

                meta = data.new_metadata(f.name, index)
                txn = data.Transaction(
                    meta=meta,
                    date=parsed_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_type,
                    narration=desc,
                    tags=set(),
                    links=set(),
                    postings=[
                        data.Posting(
                            account_cash, amount.Amount(D(amnt), self.currency), None, None, None, None
                        ),
                        data.Posting(
                            account_pnl, amount.Amount(D(amnt)*-1, self.currency), None, None, None, None
                        )
                    ],
                )

                entries.append(txn)

        return entries