import os, sys

# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

# importers located in the importers directory
from importers import custom_csv, budget, budget_today, coinspot, crypto, ioof

CONFIG = [
     custom_csv.CSVImporter(),
     budget.ActualBudgetImporter(),
     budget_today.ActualBudgetImporter(),
     coinspot.CoinSpotImporter(),
     crypto.CryptoImporter(),
     ioof.IOOFImporter()
]