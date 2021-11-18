from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import account
from beancount.core import amount
from beancount.core import flags
from beancount.core import data
from beancount.core.position import Cost

from dateutil.parser import parse

import csv
import os
import re
import yaml

# Credit to https://gist.github.com/mterwill/7fdcc573dc1aa158648aacd4e33786e8#file-importers-chase-py

class CSVImporter(importer.ImporterProtocol):
    def identify(self, f):
        return re.match('transactions_.*\.csv', os.path.basename(f.name))

    def extract(self, f):
        entries = []

        with open('config.yaml', 'r') as stream:
            try:
                yaml_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_account = row['Account']
                trans_date = parse(row['Date']).date()
                trans_payee = row['Payee']
                trans_category = row['Category']
                trans_desc = row['Memo']
                trans_amt  = row['Amount']
                trans_tag = row['Tags']
                
                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_payee,
                    narration=trans_desc,
                    tags=set(tuple([trans_tag])),
                    links=set(),
                    postings=[],
                )

                account = yaml_config['account_map'].get(trans_account) or trans_account
                category = yaml_config['account_map'].get(trans_category) or trans_category
                
                txn.postings.append(
                    data.Posting(account, amount.Amount(D(trans_amt),
                        'AUD'), None, None, None, None)
                )
                txn.postings.append(
                    data.Posting(category, None, None, None, None, None)
                )

                entries.append(txn)

        return entries
