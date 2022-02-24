
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
        return re.match("c_.*\.csv", os.path.basename(f.name))

    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                date = parse(row["Date"]).date()
                payee = row["Payee"]
                desc = row["Description"]
                
                tags = row["Tags"].lower()
                tags = tuple(tags.split(","))    

                p_dict = {
                    row["Account1"]: row["Amount1"],
                    row["Account2"]: row["Amount2"],
                    row["Account3"]: row["Amount3"],
                    row["Account4"]: row["Amount4"]
                }

                values = list(filter(lambda x: x!= "", p_dict.values()))
                check_values = sum(map(float, values))

                empty_accounts = sum(1 for i in p_dict.keys() if i == "")
                if check_values != 0:
                    pro_rata = round(-check_values/empty_accounts, 2)

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=date,
                    flag=flags.FLAG_OKAY,
                    payee=payee,
                    narration=desc,
                    tags=set(filter(None, tags)),
                    links=set(),
                    postings=[],
                )
                
                for k, v in p_dict.items():
                    if k:
                        txn.postings.append(
                            data.Posting(k, amount.Amount(D(v) if v else D(pro_rata),
                                "AUD"), None, None, None, None)
                        )

                entries.append(txn)

        return entries
