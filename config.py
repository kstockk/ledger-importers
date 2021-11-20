import os, sys, yaml

# beancount doesn't run from this directory
sys.path.append(os.path.dirname(__file__))

# importers located in the importers directory
from importers import custom_csv

with open('/bean/config.yaml', 'r') as stream:
     try:
          yaml_config = yaml.safe_load(stream)
     except yaml.YAMLError as exc:
          print(exc)

CONFIG = [
     custom_csv.CSVImporter(yaml_config)
]