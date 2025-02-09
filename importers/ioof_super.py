
from beancount.core.number import D

from beancount.core import amount
from beancount.core.position import Cost
from beancount.core import flags
from beancount.core import data

import beangulp
from beangulp import mimetypes
from beangulp.testing import main

import csv
import os
import re
from datetime import datetime
from itertools import chain, groupby
from operator import itemgetter

LEDGER_DATA_DIR = os.environ.get('LEDGER_DATA_DIR', '/Ledger')
BEAN_DATA_DIR = os.path.join(LEDGER_DATA_DIR, "mappings")
CSV_HEADER = ["Date", "Type", "Description", "Unit price", "Units", "Amount"]

class Importer(beangulp.Importer):
    def __init__(self, account, file_encoding='utf-8-sig'):
        self.importer_account = account
        self.file_encoding = file_encoding

    def identify(self, filepath):
        with open(filepath, encoding=self.file_encoding) as f:
            header = f.readline().strip().split(',')
        return header == CSV_HEADER

    def account(self, filepath):
        """Return the account against which we post transactions."""
        return self.importer_account

    def get_mappings(self):
        # Get account mapping for Budget accounts --> Ledger accounts
        # CSV should contain three columns "Budget Account, Ledger Account, Off-Budget"
        # 1nd Column (Budget Acount) will be the key
        try:
            # found_csv = os.path.exists('ioof_transactions_mapping.csv')
            # csv_path = BEAN_DATA_DIR + "/" if not found_csv else ""
            with open(BEAN_DATA_DIR + '/ioof_transactions_mappings.csv', encoding='utf-8-sig') as f:
                header = f.readline().strip()
                if re.match(header, "trans_type,account_1,account_1_value,account_2,account_2_value,asset_name_2,asset_code_2"):
                    reader = csv.reader(f)
                    account_map = {
                        rows[0]: {'account_1': rows[1], 'account_1_value': rows[2],
                                  'account_2': rows[3], 'account_2_value': rows[4],
                                  'asset_name_2': rows[5], 'asset_code_2': rows[6]} for rows in reader
                        }
            return account_map
        except:
            return False

    def get_map(self, trans_type, key):
        try:
            mappings = self.get_mappings()
            account = mappings[trans_type][key]
            return account
        except KeyError as e:
            return "no account mappings specified for {}".format(str(e))

    def extract(self, filepath, existing):
        # Create entries
        # Create transaction entries
        entries = []
        
        with open(filepath, mode='r', encoding=self.file_encoding) as f:
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

                if not "pending" in trans_type:
                    if not trans_type in ("Buys","Sells"):
                        account_1 = self.get_map(trans_type, 'account_1')
                        account_2 = self.get_map(trans_type, 'account_2')
                        ttype = trans_type
                    else:
                        account_1 = self.get_map(desc, 'account_1')
                        account_2 = self.get_map(desc, 'account_2')    
                        ttype = desc            

                    if not "no account" in account_1 or not "no account" in account_2:
                        amount_1 = D(amnt) * int(self.get_map(ttype, 'account_1_value'))
                        amount_2 = D(amnt) * int(self.get_map(ttype, 'account_2_value'))
                    else:
                        amount_1 = D(amnt)
                        amount_2 = D(amnt) * -1

                    asset_name = self.get_map(ttype, 'asset_name_2')
                    asset_code = self.get_map(ttype, 'asset_code_2')

                    cur_2 = 'AUD'
                    cost_2 = None
                    price_2 = None

                    if asset_name == desc and trans_type == "Buys":
                        amount_2 = D(units)
                        cur_2 = asset_code
                        cost_2 = Cost(D(unit_price), 'AUD', None, None)

                    if asset_name == desc and trans_type == "Sells":
                        amount_2 = D(units)
                        cur_2 = asset_code
                        cost_2 = Cost(None, 'AUD', None, None)
                        price_2 = amount.Amount(D(unit_price), 'AUD')

                    index_1 = 0 if amount_1 >= 0 else 1
                    index_2 = 1 if index_1 == 0 else 0

                    txn.postings.insert(index_1,
                        data.Posting(account_1, amount.Amount(D(amount_1),
                            'AUD'), None, None, None, None)
                    )
                    txn.postings.insert(index_2,
                        data.Posting(account_2, amount.Amount(D(amount_2),
                            cur_2), cost_2, price_2, None, None)
                    )
                    if trans_type == "Sells":
                        txn.postings.insert(3,
                        data.Posting("Income:Super:Gains", None, None, None, None, None)
                        )

                    entries.append(txn)

        return entries

