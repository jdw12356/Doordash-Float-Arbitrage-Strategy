import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
from backtest_scenarios import get_macro_profile

st.set_page_config(page_title="Doordash Float Backtest Dashboard", layout="wide")
st.title("Doordash Float Arbitrage Backtest Dashboard")

st.markdown("Run simulations across historical macro regimes (2020, 2022, 2023) to test resilience and alpha.")

# Sidebar
with st.sidebar:
    st.header("Simulation Settings")
    days = st.slider("Simulation Days", 30, 365, 180)
    daily_spend_base = st.number_input("Base Daily Spend ($)", 10.0, 500.0, 85.71, step=1.0)
    selected_year = st.selectbox("Macro Backtest Year", [2020, 2022, 2023])
    simulate_google_sheets = st.checkbox("Enable Google Sheets Export", value=False)

# Main Logic
def simulate_strategy(days=365, daily_spend_base=85.71, year=2023):
    start_date = datetime.today()
    active_floats = []
    daily_summary = []
    cumulative_profit = 0
    daily_cash_yield = 0.0375 / 365
    daily_bond_yield = 0.055 / 365
    payment_offsets = [0, 14, 28, 42]

    cpi_growth, vol_mult = get_macro_profile(year, days)

    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_of_week = current_date.weekday()
        weekend_boost = 1.2 if day_of_week >= 5 else 1.0
        seasonal_drift = 1 + cpi_growth[i] * 100  # inflation-adjusted
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

        option_yield = ((total_active_float / 1000) * (7 / 7)) * (1 + vol_mult[i] * 10)
        daily_profit += option_yield

        payments_due_today = sum(f["amount"] * 0.25 for f in active_floats for offset in payment_offsets if f["start_date"] + timedelta(days=offset) == current_date)
        cumulative_profit += daily_profit

        daily_summary.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "New Float ($)": new_float,
            "Active Float Total ($)": round(total_active_float, 2),
            "Daily Profit ($)": round(daily_profit, 2),
            "Cumulative Profit ($)": round(cumulative_profit, 2),
            "Payments Due Today ($)": round(payments_due_today, 2),
            "Multiplier": round(vol_mult[i] * 10, 3)
        })

    df = pd.DataFrame(daily_summary)
    df["Daily Return"] = df["Daily Profit ($)"] / df["Active Float Total ($)"]
    df["Daily Return"] = df["Daily Return"].replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

df = simulate_strategy(days, daily_spend_base, selected_year)

# Sharpe/Sortino
avg_return = df["Daily Return"].mean()
std_return = df["Daily Return"].std()
downside_dev = df[df["Daily Return"] < 0]["Daily Return"].std()

sharpe = (avg_return - 0.01 / 365) / std_return if std_return else 0
sortino = (avg_return - 0.01 / 365) / downside_dev if downside_dev else 0

st.metric("Final Cumulative Profit", f"${df['Cumulative Profit ($)'].iloc[-1]:,.2f}")
st.metric("Max Active Float", f"${df['Active Float Total ($)'].max():,.2f}")
st.metric("Sharpe Ratio", f"{sharpe:.2f}")
st.metric("Sortino Ratio", f"{sortino:.2f}")

st.line_chart(df.set_index("Date")[["Cumulative Profit ($)", "Active Float Total ($)"]])
st.line_chart(df.set_index("Date")["Multiplier"])
st.dataframe(df, use_container_width=True)

if simulate_google_sheets:
    st.warning("Upload your service account key JSON and enable export.")