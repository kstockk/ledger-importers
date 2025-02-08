from beancount.core.number import D
from beancount.loader import importer
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

class CSVImporter(importer.Importer):
    def identify(self, f):
        return re.match("c_.*\.csv", os.path.basename(f.name))

    def extract(self, f):
        entries = []

        with open(f.name) as f:
            for index, row in enumerate(csv.DictReader(f)):
                trans_date = parse(row["Date"]).date() if row["Date"] != "" else date.today()
                flag= row["Flag"]
                payee = row["Payee"]
                desc = row["Description"]
                
                tags = row["Tags"].lower()
                tags = tuple(tags.split(","))    

                p_dict = collections.defaultdict(list)
                for k, v in (
                    (row["Account1"], row["Amount1"] if row["Amount1"] else 0),
                    (row["Account2"], row["Amount2"] if row["Amount2"] else 0),
                    (row["Account3"], row["Amount3"] if row["Amount3"] else 0),
                    (row["Account4"], row["Amount4"] if row["Amount4"] else 0)
                    ):
                    p_dict[k].append(v)

                values = list(p_dict.values())
                check_values = sum(sum(map(Decimal, x)) for x in values)

                empty_accounts = sum(1 for i in p_dict.keys() if i == "")
                
                if check_values != 0:
                    pro_rata = D(-check_values/empty_accounts)
                    pro_rata = pro_rata.quantize(Decimal(10) ** -2).normalize()

                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=trans_date,
                    flag=flags.FLAG_WARNING if flag == "!" else flags.FLAG_OKAY,
                    payee=payee,
                    narration=desc,
                    tags=set(filter(None, tags)),
                    links=set(),
                    postings=[],
                )
                
                for key, values in p_dict.items():
                    if key:
                        if(isinstance(values, list)):
                            for value in values: 
                                txn.postings.append(
                                    data.Posting(key, amount.Amount(D(value) if value else pro_rata,
                                        "AUD"), None, None, None, None)
                                )

                entries.append(txn)

        return entries
