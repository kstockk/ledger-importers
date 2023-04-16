# beancount_importers

Custom beancount/fava importers...

## Master Beancount Custom Entries

Ensure the following two custome entries are in your master.beancount file

```
2017-07-01 custom "fava-option" "import-config" "/bean/config/config.py"
2017-07-01 custom "fava-option" "import-dirs" "import_files/"
```

## To Run/Test

```
bean-extract config.py importers/custom_csv/c_sample.csv 
```

## Known Issues

- For the budget importer - Cannot have the same description but one of the leg has a #tag. It doesn't work...