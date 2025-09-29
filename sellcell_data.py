import pandas as pd

EXCEL_PATH = "SellCell.xlsx"

def load_sellcell_data():
    # Read Excel with two header rows (condition, metric)
    sheets = pd.read_excel(EXCEL_PATH, sheet_name=None, header=[0,1])
    return sheets

def get_device_column(df):
    for col in df.columns:
        if (isinstance(col, tuple) and col[0].lower() == "device") or (isinstance(col, str) and col.lower() == "device"):
            return col
    raise KeyError(f"Could not find 'Device' column in columns: {df.columns.tolist()}")

def get_all_devices():
    sheets = load_sellcell_data()
    devices = set()
    for df in sheets.values():
        device_col = get_device_column(df)
        devices.update(str(x) for x in df[device_col].dropna().unique())
    return list(devices)

def get_all_conditions(df):
    return [cond for cond in df.columns.levels[0] if cond not in ("Device", "MSRP", "Launch Year")]

def get_sellcell_price(device_model: str, condition: str = None, storage: str = None, mode: str = "exact") -> dict:
    """
    mode = "exact" → return price for a given condition
    mode = "max"   → return highest price across all conditions
    """
    sheets = load_sellcell_data()
    if condition:
        condition = condition.title()

    for brand, df in sheets.items():
        device_col = get_device_column(df)
        # Match device row (and storage if provided)
        mask = df[device_col].astype(str).str.lower().str.strip() == device_model.lower().strip()
        if storage:
            mask &= df[device_col].astype(str).str.contains(storage, case=False, na=False)

        row = df[mask]
        if not row.empty:
            msrp = row.iloc[0].get(('MSRP', ''), "")
            launch_year = row.iloc[0].get(('Launch Year', ''), "")

            if mode == "max":
                max_price = None
                for cond in df.columns.levels[0]:
                    if cond in ("Device", "MSRP", "Launch Year"):
                        continue
                    try:
                        price = row.iloc[0][(cond, "Top Price")]
                        if pd.notna(price) and (max_price is None or price > max_price):
                            max_price = price
                    except Exception:
                        continue
                return {"price": max_price, "msrp": msrp, "launch_year": launch_year, "brand": brand}

            elif condition:
                try:
                    price = row.iloc[0][(condition, "Top Price")]
                    depr = row.iloc[0][(condition, "Depr.")]
                    depr_pct = row.iloc[0][(condition, "%")]
                except KeyError:
                    return {}
                return {
                    "price": price,
                    "depreciation": depr,
                    "depreciation_pct": depr_pct,
                    "msrp": msrp,
                    "launch_year": launch_year,
                    "brand": brand
                }
    return {}
