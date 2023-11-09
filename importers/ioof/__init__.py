
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

CSV_HEADER = ["Date", "Type", "Description", "Unit price", "Units", "Amount"]

class IOOFImporter(importer.ImporterProtocol):
    def __init__(self, file_encoding='utf-8-sig'):
        self.file_encoding = file_encoding

    def identify(self, file_):
        with open(file_.name, encoding=self.file_encoding) as f:
            header = f.readline().strip().split(',')
        return header == CSV_HEADER

    def extract(self, file_):
        # Create entries
        # Create transaction entries
        entries = []
        
        with open(file_.name, mode='r', encoding=self.file_encoding) as f:
            for index, row in enumerate(csv.DictReader(f)):
                parsed_date = datetime.strptime(row["Date"], '%d/%m/%Y').date()
                trans_type = row["Type"]
                desc = row["Description"]
                unit_price = row["Unit price"]
                units = row["Units"]
                amnt = row["Amount"]

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=parsed_date,
                    flag=flags.FLAG_OKAY,
                    payee=trans_type,
                    narration=desc,
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                if trans_type == "Deposit":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Income:Super:Concessional-Contributions:IOOF", amount.Amount(D(amnt)*-1,
                            'AUD'), None, None, None, None)
                    )

                if trans_type == "Tax":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Expenses:Super:Tax:IOOF-Employer-Super", amount.Amount(D(amnt)*-1,
                            'AUD'), None, None, None, None)
                    )

                if trans_type == "Fees & costs":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Expenses:Super:Fees:IOOF-Employer-Super", amount.Amount(D(amnt)*-1,
                            'AUD'), None, None, None, None)
                    )

                if trans_type == "Insurance":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Expenses:Super:Insurance:IOOF-Employer-Super", amount.Amount(D(amnt)*-1,
                            'AUD'), None, None, None, None)
                    )

                if trans_type == "Buys":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:IOF0097AU", amount.Amount(D(units),
                            'IOF0097AU'), Cost(D(unit_price), 'AUD', None, None), None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )

                if trans_type == "Income":
                    txn.postings.insert(0,
                        data.Posting("Assets:Super:IOOF-Employer-Super:Cash", amount.Amount(D(amnt),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Income:Super:Income", amount.Amount(D(amnt)*-1,
                            'AUD'), None, None, None, None)
                    )

                entries.append(txn)

        return entries