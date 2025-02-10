import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Function to Optimize EV Charging
def optimized_ev_charging(plug_in_time, current_soc, target_soc, full_charge_minutes, battery_capacity, deadline):
    required_percentage = target_soc - current_soc
    if required_percentage <= 0:
        return "No charging needed."

    minutes_per_percent = full_charge_minutes / 100.0
    required_charge_minutes = required_percentage * minutes_per_percent

    pricing_intervals = [
        {"start": "06:00", "end": "18:00", "price": 9.0},
        {"start": "18:00", "end": "22:00", "price": 12.5},
        {"start": "22:00", "end": "06:00", "price": 10.0}
    ]

    available_intervals = []

    def time_from_str(t_str):
        return datetime.strptime(t_str, "%H:%M").time()

    current_day = plug_in_time.date()
    deadline_day = deadline.date()

    day = current_day
    while day <= deadline_day:
        for interval in pricing_intervals:
            base_start = datetime.combine(day, time_from_str(interval["start"]))
            base_end = datetime.combine(day, time_from_str(interval["end"]))
            if base_end <= base_start:
                base_end += timedelta(days=1)

            effective_start = max(plug_in_time, base_start)
            effective_end = min(deadline, base_end)

            if effective_end > effective_start:
                available_intervals.append({
                    "start": effective_start,
                    "end": effective_end,
                    "price": interval["price"]
                })
        day += timedelta(days=1)

    if not available_intervals:
        return "No available time intervals."

    available_intervals.sort(key=lambda x: x["price"])

    remaining_charge_minutes = required_charge_minutes
    allocated_intervals = []

    for interval in available_intervals:
        duration = (interval["end"] - interval["start"]).total_seconds() / 60.0
        if duration <= 0:
            continue

        allocated_minutes = min(duration, remaining_charge_minutes)
        allocated_intervals.append({
            "Start Time": interval["start"],
            "End Time": interval["start"] + timedelta(minutes=allocated_minutes),
            "Price (₹/kWh)": interval["price"],
            "Charging Duration (min)": allocated_minutes
        })
        remaining_charge_minutes -= allocated_minutes

        if remaining_charge_minutes <= 0:
            break

    if remaining_charge_minutes > 0:
        return "Not enough time to reach target SOC."

    allocated_intervals.sort(key=lambda x: x["Start Time"])
    return allocated_intervals

# Streamlit App UI
st.title("⚡ Optimized EV Charging Scheduler")

# Date & Time Input Fix
date = st.date_input("Plug-in Date", datetime(2025, 2, 10).date())
time = st.time_input("Plug-in Time", datetime(2025, 2, 10, 17, 0).time())
plug_in_time = datetime.combine(date, time)

deadline_date = st.date_input("Charging Deadline Date", datetime(2025, 2, 11).date())
deadline_time = st.time_input("Charging Deadline Time", datetime(2025, 2, 11, 4, 0).time())
deadline = datetime.combine(deadline_date, deadline_time)

# Charging Inputs
current_soc = st.slider("Current SOC (%)", 0, 100, 20)
target_soc = st.slider("Target SOC (%)", 0, 100, 80)
full_charge_minutes = st.number_input("Full Charge Time (minutes)", value=600)
battery_capacity = st.number_input("Battery Capacity (kWh)", value=50)

# Run Optimization
if st.button("🔍 Optimize Charging Schedule"):
    result = optimized_ev_charging(plug_in_time, current_soc, target_soc, full_charge_minutes, battery_capacity, deadline)

    if isinstance(result, str):
        st.warning(result)
    else:
        df = pd.DataFrame(result)
        st.dataframe(df)
