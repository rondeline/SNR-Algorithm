# Subject information template

The header-only `subject_info_NIH.csv` describes the metadata columns accessed by the current histogram script. It contains no participant data.

| Column | Meaning / use |
| --- | --- |
| `Subject_Number` | Text identifier matching the workbook sheet prefix, such as the naming pattern `S<number>` |
| `Group` | Group label; the current script includes special handling for `HL` |
| `Subgroup` | Subgroup label; the current script includes combined handling of `HA` and `CI` |
| `Threshold_Score` | Optional numeric threshold used by the histogram logic; leave blank when unavailable |

To create an empty Excel input locally, run from the repository root:

```bash
python tools/create_subject_info_template.py
```

It writes `scripts/FinalPythonScripts/subject_info_NIH.xlsx`, with headers on the first row, no participant rows, and no extra instructions sheet. It refuses to overwrite an existing workbook. Populate it locally before using Step 7. The workbook is excluded by `.gitignore`.

Alternatively, open the CSV in Excel and save it as an Excel workbook at the same required path. Keep headers exactly as shown. No output-master templates are needed: Step 2 creates the local master workbooks from successful MATLAB results. Step 7 still needs the missing Each_Day helper described in `docs/KNOWN_LIMITATIONS.md`.
