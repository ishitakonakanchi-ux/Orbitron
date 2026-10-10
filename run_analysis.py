
import json
import os
from datetime import datetime, timezone

import pandas as pd

SPREADSHEET_ID = "1Xo6oSmDzJvRmZ6sibyM34MXb0OlUT-whAIW5sfG_9MY"
CREDENTIALS    = "credentials.json"
RESULTS_CSV    = "final_risk_output.csv"
CATALOG_CSV    = "satellites.csv"
DRY_RUN        = False

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# sheet column headers
COLUMNS = {
    "sat_a":                   "Sat 1",
    "sat_b":                   "Sat 2",
    "kalman_min_dist_km":      "Miss Distance (km)",
    "time_to_min_minutes":     "TCA (min)",
    "risk_tier":               "Risk Tier",
    "conjunction_probability": "Pc %",
    "display_risk_pct":        "Model Score",
}


def to_matrix(df):
    """DataFrame -> list of lists, with NaN and numpy types stripped out.

    Gspread sends JSON, and numpy int64/float64 cant be serialized. 
    This converts them and turns NaN into null, which is then blanked.
    """
    rows = json.loads(df.to_json(orient="values"))
    return [df.columns.tolist()] + [["" if v is None else v for v in r] for r in rows]


def write_tab(spreadsheet, title, matrix):
    #one batched write for whole tab.
    
    rows, cols = len(matrix), len(matrix[0])
    try:
        ws = spreadsheet.worksheet(title)
        if ws.row_count < rows or ws.col_count < cols:
            ws.resize(rows=rows + 50, cols=max(cols, ws.col_count))
        ws.clear()
    except Exception:
        ws = spreadsheet.add_worksheet(title=title, rows=rows + 50, cols=cols)
    ws.update(values=matrix, range_name="A1")
    print(f"  {title}: {rows - 1} rows")
    return ws


results = pd.read_csv(RESULTS_CSV)[list(COLUMNS)].rename(columns=COLUMNS)
results["Last Updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# catalog tab keeps every satellite in the dropdown. 
# otherwise,  page builds its list from the pair rows, so it shrinks to only flagged satellites.
catalog = pd.read_csv(CATALOG_CSV)[["name", "norad_id"]] \
    if os.path.exists(CATALOG_CSV) else pd.DataFrame(columns=["name", "norad_id"])

results_matrix = to_matrix(results)
catalog_matrix = to_matrix(catalog)
print(f"{len(results)} pairs, {len(catalog)} satellites")

if DRY_RUN:
    print("\nDRY RUN — set DRY_RUN = False to write.")
    for row in results_matrix[:4]:
        print("  " + " | ".join(str(c) for c in row))
else:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(CREDENTIALS, scopes=SCOPES)
    spreadsheet = gspread.authorize(creds).open_by_key(SPREADSHEET_ID)
    print(f"Connected to {spreadsheet.title!r}")

    ws_r = write_tab(spreadsheet, "Results", results_matrix)
    ws_c = write_tab(spreadsheet, "Catalog", catalog_matrix)

    print(f'\nRESULTS_GID = "{ws_r.id}"\nCATALOG_GID = "{ws_c.id}"')