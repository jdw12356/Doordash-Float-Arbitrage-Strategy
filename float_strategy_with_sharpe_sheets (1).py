
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
import yfinance as yf
import requests
import matplotlib.pyplot as plt
import seaborn as sns

# Optional: Google Sheets integration (requires gspread and oauth2client)
def push_to_google_sheets(df, sheet_name="DoordashFloatResults", creds_file="your-key.json"):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)

        try:
            sheet = client.open(sheet_name).sheet1
        except gspread.SpreadsheetNotFound:
            sheet = client.create(sheet_name).sheet1

        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        print(f"Data pushed to Google Sheets: https://docs.google.com/spreadsheets/d/{sheet.spreadsheet.id}")
    except Exception as e:
        print(f"Google Sheets sync failed: {e}")

def compute_sharpe_sortino(df, risk_free_rate=0.01):
    df["Daily Return"] = df["Daily Profit ($)"] / df["Active Float Total ($)"]
    df["Daily Return"] = df["Daily Return"].replace([np.inf, -np.inf], np.nan).fillna(0)

    avg_return = df["Daily Return"].mean()
    std_dev = df["Daily Return"].std()
    downside_dev = df[df["Daily Return"] < 0]["Daily Return"].std()

    sharpe = (avg_return - risk_free_rate / 365) / std_dev if std_dev else 0
    sortino = (avg_return - risk_free_rate / 365) / downside_dev if downside_dev else 0

    return sharpe, sortino

def simulate_strategy(days=365, daily_spend_base=85.71):
    start_date = datetime.today()
    active_floats = []
    daily_summary = []
    cumulative_profit = 0
    daily_cash_yield = 0.0375 / 365
    daily_bond_yield = 0.055 / 365
    payment_offsets = [0, 14, 28, 42]

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()
        weekend_boost = 1.2 if day_of_week >= 5 else 1.0
        seasonal_drift = 1 + 0.05 * np.sin(i / 50.0)
        new_float = round(daily_spend_base * random.uniform(0.85, 1.15) * weekend_boost * seasonal_drift, 2)

        active_floats.append({
            "start_date": current_date,
            "end_date": current_date + timedelta(days=42),
            "amount": new_float
        })

        daily_profit = 0
        total_active_float = 0
        for f in active_floats:
            if f["start_date"] <= current_date < f["end_date"]:
                bond_part = f["amount"] * 0.75
                cash_part = f["amount"] * 0.25
                daily_profit += bond_part * daily_bond_yield + cash_part * daily_cash_yield
                total_active_float += f["amount"]

        payments_due_today = sum(f["amount"] * 0.25 for f in active_floats for offset in payment_offsets if f["start_date"] + timedelta(days=offset) == current_date)
        cumulative_profit += daily_profit

        daily_summary.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "New Float ($)": new_float,
            "Active Float Total ($)": round(total_active_float, 2),
            "Daily Profit ($)": round(daily_profit, 2),
            "Cumulative Profit ($)": round(cumulative_profit, 2),
            "Payments Due Today ($)": round(payments_due_today, 2)
        })

    df = pd.DataFrame(daily_summary)
    return df

if __name__ == "__main__":
    df = simulate_strategy()
    print(df)

    sharpe, sortino = compute_sharpe_sortino(df)
    print(f"Sharpe Ratio: {sharpe:.3f}")
    print(f"Sortino Ratio: {sortino:.3f}")

    # Optional Google Sheets sync
    # push_to_google_sheets(df, creds_file="your-key.json")

    plt.figure(figsize=(12, 6))
    sns.lineplot(x="Date", y="Cumulative Profit ($)", data=df)
    plt.title("Cumulative Profit Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
