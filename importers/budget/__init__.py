
from beancount.core.number import D
from beancount.ingest import importer
from beancount.core import amount
from beancount.core import flags
from beancount.core import data

import csv
import os
import re
from dateutil.parser import parse
from itertools import groupby
from operator import itemgetter

CSV_HEADER = "Account,Date,Payee,Notes,Category,Amount"
BEAN_DATA_DIR = "/bean/data"
ACCOUNT_MAP = "account_map.csv"

class ActualBudgetImporter(importer.ImporterProtocol):
    def __init__(self, currency='AUD', file_encoding='utf-8'):
        self.currency = currency
        self.file_encoding = file_encoding

    def identify(self, file_):
        with open(file_.name, encoding=self.file_encoding) as f:
            header = f.readline().strip()
        
        return re.match(header, CSV_HEADER)

    def get_account_map(self):
        # Get account mapping for Budget accounts --> Ledger accounts
        # CSV should contain three columns "Budget Account, Ledger Account, Off-Budget"
        # 1nd Column (Budget Acount) will be the key
        try:
            found_csv = os.path.exists(ACCOUNT_MAP)
            csv_path = BEAN_DATA_DIR + "/" if not found_csv else ""
            with open(csv_path + ACCOUNT_MAP) as f:
                reader = csv.reader(f)
                account_map = {rows[0]:{'Ledger Account': rows[1], 'Off-Budget': rows[2]} for rows in reader}
            return account_map
        except:
            return False

    def get_ledger_account(self, account):
        try:
            account_map = self.get_account_map()
            return account_map[account]["Ledger Account"]
        except KeyError:
            return account

    def is_off_budget(self, account):
        try:
            account_map = self.get_account_map()
            if account_map[account]["Off-Budget"] == "Y":
                return True
        except KeyError:
            return False

    def extract(self, f):
        # Store csv rows in dict
        with open(f.name, mode='r') as f:
            rows = []
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        # Clean up data
        for index, row in enumerate(rows):
            # Change accounts based on account mapping details
            row["Account"] = self.get_ledger_account(row["Account"])
            row["Category"] = self.get_ledger_account(row["Category"])

            # Create key with absolute values
            row["Abs"] = abs(D(row["Amount"]))

            # Parse notes for tags
            parse_notes = row["Notes"].split("#", 1)
            row["Notes"] = parse_notes[0].strip()
            row["Tags"] = ""
            if len(parse_notes) > 1:
                tags = parse_notes[1]
                row["Tags"] = tags.replace("#", "").lower()
                row["Tags"] = tuple(row["Tags"].split(", "))

            # If payee is a Starting Balance
            # Need this as off-budget accounts will not have a category
            # Need step is to assume no category is a transfer
            if row["Payee"] == "Starting Balance":
                row["Category"] = "Starting Balance"

            # Rows with no category are assumed to be transfers
            # Create seperate lists for non_transfers and transfers            
            if not row['Category'] and not self.is_off_budget(row["Account"]):
                row['Notes'] = self.get_ledger_account(row['Payee'])
                row['Payee'] = "Transfer"

            # If payee is an Off-Budget account then assume it is a transfer
            # Replace the Notes will the Payee
            if self.is_off_budget(row["Payee"]):
                row['Notes'] = self.get_ledger_account(row["Payee"])
                row["Payee"] = "Transfer"

        # Group rows for postings if the specified columns match
        transactions_grouper = itemgetter("Date", "Account", "Payee", "Notes", "Tags")
        transactions = sorted(rows, key = transactions_grouper)

        # Create entries
        # Create transaction entries
        entries = []
        for index, (key, values) in enumerate(groupby(transactions, key = transactions_grouper)):
            if not key[2] in ["Transfer", "Starting Balance"]:
                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=parse(key[0]).date(),
                    flag=flags.FLAG_OKAY,
                    payee=key[2],
                    narration=key[3],
                    tags=set(filter(None, key[4])),
                    links=set(),
                    postings=[],
                )

                total = 0
                for value in values:
                    txn.postings.append(
                        data.Posting(value["Category"], amount.Amount(D(value["Amount"])*-1,
                            "AUD"), None, None, None, None)
                    )
                    total += D(value["Amount"])

                txn.postings.insert(0,
                    data.Posting(key[1], amount.Amount(total,
                        self.currency), None, None, None, None)
                )

                entries.append(txn)

        transger_grouper = itemgetter("Date", "Payee", "Abs")
        transfers = sorted(rows, key = transger_grouper)

        # Create transfer entries
        for index, (key, values) in enumerate(groupby(transfers, key = transger_grouper)):
            if key[1] == "Starting Balance":
                meta = data.new_metadata(f.name, index)

                for value in values:
                    txn = data.Balance(
                        meta=meta,
                        date=parse(value["Date"]).date(),
                        account=value["Account"],
                        amount=amount.Amount(D(value["Amount"]), self.currency),
                        tolerance=None,
                        diff_amount=None
                    )

                entries.append(txn)
            
            if key[1] == "Transfer":
                meta = data.new_metadata(f.name, index)

                txn = data.Transaction(
                    meta=meta,
                    date=parse(key[0]).date(),
                    flag=flags.FLAG_OKAY,
                    payee=None,
                    narration=key[1],
                    tags=set(),
                    links=set(),
                    postings=[],
                )

                total = 0
                for value in values:
                    position = 0 if D(value["Amount"]) < 0 else 1
                    txn.postings.insert(position,
                        data.Posting(value["Account"], amount.Amount(D(value["Amount"]),
                            self.currency), None, None, None, None)
                    )
                    total += D(value["Amount"])
                    to_account = value["Notes"]

                # Complete transfer journal using the account specified in the Notes if journal doesn't add up to 0
                # This will happen if you only export for a single account instead of all accounts
                x = 1 if total < 0 else 0
                if total != D(0):
                    txn.postings.insert(x,
                        data.Posting(to_account, amount.Amount(-total,
                            self.currency), None, None, None, None)
                    )

                entries.append(txn)

        return entries