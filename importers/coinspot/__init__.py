
from beancount.core.number import D
from beancount.loader import importer
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

CSV_HEADER = ["Transaction Date","Type","Market","Amount","Rate inc. fee","Rate ex. fee","Fee","Fee AUD (inc GST)","GST AUD","Total AUD","Total (inc GST)"]

class CoinSpotImporter(importer.Importer):
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
                parsed_date = datetime.strptime(row["Transaction Date"], '%d/%m/%Y').date()
                trans_type = row["Type"]
                market = row["Market"]
                amnt = row["Amount"]
                rate_inc = row["Rate inc. fee"]
                rate_ex = row["Rate ex. fee"]
                fee = row["Fee"]
                total_aud = row["Total AUD"]

                narrate = " ".join([trans_type,amnt,market,"at",rate_inc,"AUD (incl. fee)"])
                meta = data.new_metadata(f.name, index, {"rate_ex": rate_ex + ' AUD', "brokerage": fee})

                coin = market.split("/")[0]

                txn = data.Transaction(
                    meta=meta,
                    date=parsed_date,
                    flag=flags.FLAG_OKAY,
                    payee=None,
                    narration=narrate,
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                if trans_type == "Buy":
                    txn.postings.insert(0,
                        data.Posting("Assets:Crypto:CoinSpot:" + coin, amount.Amount(D(amnt),
                            coin), Cost(D(rate_inc), 'AUD', None, None), None, None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Assets:Crypto:CoinSpot:Cash", amount.Amount(D(total_aud)*-1,
                            'AUD'), None, None, None, None)
                    )
                    entries.append(txn)

                if trans_type == "Sell":
                    txn.postings.insert(0,
                        data.Posting("Assets:Crypto:CoinSpot:" + coin, amount.Amount(D(amnt)*-1,
                            coin), Cost(None, 'AUD', None, None), amount.Amount(D(rate_inc), 'AUD'), None, None)
                    )
                    txn.postings.insert(1,
                        data.Posting("Assets:Crypto:CoinSpot:Cash", amount.Amount(D(total_aud),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(2,
                        data.Posting("Income:Crypto:Gains", None, None, None, None, None)
                    )
                    entries.append(txn)

        return entries