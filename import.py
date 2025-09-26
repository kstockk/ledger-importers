import os, sys

# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

from importers import actual_budget
from importers import ioof_super
from importers import upwork

import beangulp

CONFIG = [
    actual_budget.Importer("Assets:Account"),
    ioof_super.Importer("Assets:Account2"),
    upwork.Importer("Assets:Freelance:Upwork-Account", "USD")
]

if __name__ == '__main__':
    ingest = beangulp.Ingest(CONFIG)
    ingest()