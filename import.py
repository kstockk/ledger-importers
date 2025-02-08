
from importers import actual_budget
from importers import ioof_super

import beangulp

importers = [
    actual_budget.Importer("Assets:Account"),
    ioof_super.Importer("Assets:Account2")
]

if __name__ == '__main__':
    ingest = beangulp.Ingest(importers)
    ingest()