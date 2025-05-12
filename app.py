
import streamlit as st
import pandas as pd
from datetime import time, timedelta

def is_night_shift(t):
    return t >= time(19, 0) or t <= time(6, 49, 59)

def assign_shift_number(dt, base_shift_start, starting_shift_number):
    if dt.time() <= time(6, 49, 59):
        shift_date = dt.date() - timedelta(days=1)
    else:
        shift_date = dt.date()
    shift_number = (pd.Timestamp(shift_date) - pd.Timestamp(base_shift_start.date())).days + starting_shift_number
    return f'SHIFT {shift_number}'

st.title("Alarm Raw Data Cleaner")
st.write("Upload a CSV file. Rows outside 7:00 PM to 6:49:59 AM are removed. Shift labels are automatically assigned.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")
starting_shift = st.number_input("Start from SHIFT number:", min_value=1, value=1)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if 'Date/Time' not in df.columns:
        st.error("The uploaded CSV must contain a 'Date/Time' column.")
    else:
        df['Date/Time'] = pd.to_datetime(df['Date/Time'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Date/Time'])

        df['TimeOnly'] = df['Date/Time'].dt.time
        filtered_df = df[df['TimeOnly'].apply(is_night_shift)].drop(columns=['TimeOnly'])

        if not filtered_df.empty:
            base_dt = filtered_df['Date/Time'].min()
            if base_dt.time() <= time(6, 49, 59):
                base_shift_start = (base_dt - pd.Timedelta(days=1)).replace(hour=19, minute=0, second=0)
            else:
                base_shift_start = base_dt.replace(hour=19, minute=0, second=0)

            filtered_df['Shift'] = filtered_df['Date/Time'].apply(
                lambda dt: assign_shift_number(dt, base_shift_start, starting_shift)
            )

            st.success(f"Filtered down to {len(filtered_df)} rows.")
            st.dataframe(filtered_df)

            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Cleaned CSV",
                data=csv,
                file_name='cleaned_nightshift_with_shifts.csv',
                mime='text/csv'
            )
        else:
            st.warning("No rows matched the night shift window.")
