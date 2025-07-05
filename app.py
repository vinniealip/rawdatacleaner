import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

def is_within_range(t, start_t, end_t):
    if start_t < end_t:
        return start_t <= t <= end_t
    else:
        return t >= start_t or t <= end_t

def assign_shift_number(dt, base_shift_start, starting_shift_number):
    if dt.time() <= shift_end:
        shift_date = dt.date() - timedelta(days=1)
    else:
        shift_date = dt.date()
    shift_number = (pd.Timestamp(shift_date) - pd.Timestamp(base_shift_start.date())).days + starting_shift_number
    return f'SHIFT {shift_number}'

st.title("Alarm Raw Data Cleaner")
st.write("Upload a CSV file. Rows outside your defined time range are removed. Shift labels are automatically assigned.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")
starting_shift = st.number_input("Start from SHIFT number:", min_value=1, value=1)

start_time_str = st.text_input("Enter start time (HH:MM:SS, 24-hour)", value="19:00:00")
end_time_str = st.text_input("Enter end time (HH:MM:SS, 24-hour)", value="06:49:59")

try:
    shift_start = datetime.strptime(start_time_str, "%H:%M:%S").time()
    shift_end = datetime.strptime(end_time_str, "%H:%M:%S").time()
except ValueError:
    st.error("Invalid time format. Please use HH:MM:SS format.")
    shift_start, shift_end = time(19, 0), time(6, 49, 59)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if 'Date/Time' not in df.columns:
        st.error("The uploaded CSV must contain a 'Date/Time' column.")
    else:
        # Attempt to parse common formats flexibly
        def parse_datetime_flexibly(date_str):
            for fmt in [
                "%d/%m/%Y %I:%M:%S %p", "%d/%m/%Y %I:%M %p",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
                "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M",
                "%m/%d/%Y %I:%M %p", "%Y-%m-%d %H:%M:%S"
            ]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return pd.NaT

        df['Date/Time'] = df['Date/Time'].astype(str).apply(parse_datetime_flexibly)
        df = df.dropna(subset=['Date/Time'])

        # Sort by Date/Time ascending (oldest to newest)
        df = df.sort_values(by='Date/Time')

        if not df.empty:
            df['TimeOnly'] = df['Date/Time'].dt.time
            filtered_df = df[df['TimeOnly'].apply(lambda t: is_within_range(t, shift_start, shift_end))].copy()

            if 'TimeOnly' in filtered_df.columns:
                filtered_df.drop(columns=['TimeOnly'], inplace=True)

            if not filtered_df.empty:
                base_dt = filtered_df['Date/Time'].min()
                if base_dt.time() <= shift_end:
                    base_shift_start = (base_dt - pd.Timedelta(days=1)).replace(hour=shift_start.hour, minute=shift_start.minute, second=shift_start.second)
                else:
                    base_shift_start = base_dt.replace(hour=shift_start.hour, minute=shift_start.minute, second=shift_start.second)

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
                st.warning("No rows matched the selected time window.")
        else:
            st.warning("No valid rows after parsing Date/Time.")
