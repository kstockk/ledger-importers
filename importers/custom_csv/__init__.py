from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core import data
from beancount.core.position import Cost

from dateutil.parser import parse

from titlecase import titlecase

import csv
import os
import re

# Credit to https://gist.github.com/mterwill/7fdcc573dc1aa158648aacd4e33786e8#file-importers-chase-py

class CSVImporter(importer.ImporterProtocol):
    def identify(self, f):
        return re.match('test.csv', os.path.basename(f.name))

    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_acc = titlecase(row['Account'])
                trans_date = parse(row['Date']).date()
                trans_payee = titlecase(row['Payee'])
                trans_cat = titlecase(row['Category'])
                trans_desc = titlecase(row['Memo'])
                trans_amt  = row['Amount']
                
                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_payee,
                    narration=trans_desc,
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                txn.postings.append(
                    data.Posting(trans_acc, amount.Amount(D(trans_amt),
                        'AUD'), None, None, None, None)
                )
                txn.postings.append(
                    data.Posting(trans_cat, None, None, None, None, None)
                )

                entries.append(txn)

        return entries
