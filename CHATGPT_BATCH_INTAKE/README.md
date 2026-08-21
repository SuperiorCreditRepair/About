# ChatGPT batch intake

This folder is the expected online landing place for the uniqueness corpus.

Put all 8 files here (unzipped):

- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_01_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_02_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_03_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_04_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_05_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_06_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_07_OF_08.csv`
- `UNIQUENESS_CORPUS/UNIQUENESS_CORPUS_08_OF_08.csv`

The matching `.zip` files already live in the repository root because GitHub's website upload limit is 25 MB and two of the raw CSVs are larger than that.

## Local Windows layout

- Python stays on C:
- The Superior Credit Rebuild share stays on D:
- Temp/cache should stay on D:, not C:

Example:

```bat
C:\Python312\python.exe tools\chatgpt_page_audit.py --corpus-dir "D:\CHATGPT_BATCH_INTAKE\UNIQUENESS_CORPUS" --out-dir "D:\Temp\scr_chatgpt_audit"
```

Do not overwrite `CLEARED_PRODUCTION` pages or sequences 1–5.
