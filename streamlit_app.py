import io
import sys
import contextlib
import streamlit as st
import pandas as pd

from graylog import get_install_create_vector_check_logs
from clickhouse import get_install_create_vector_check_rt


def parse_message(message: str) -> dict:
    parts = message.split()
    data = {}

    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            data[key] = value

    return {
        'payment_account_id': data.get('payment_account_id'),
        'user_id': data.get('user_id'),
        'unified_id': data.get('unified_id'),
        'device_id': data.get('device_id'),
    }


def run_check(hours: int = 24):
    # capture stdout
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        input_file = get_install_create_vector_check_logs(hours)
        output_file = "parsed_graylog_logs.csv"

        import csv

        with open(input_file, newline='', encoding='utf-8') as infile, \
                open(output_file, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile)

            if not reader.fieldnames:
                print("No data found in the input file.")
                return buf.getvalue()

            fieldnames = list(reader.fieldnames) + [
                'payment_account_id',
                'user_id',
                'unified_id',
                'device_id'
            ]

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                parsed = parse_message(row['message'])
                row.update(parsed)
                writer.writerow(row)

        graylog_df = pd.read_csv(output_file)
        print(graylog_df.head())

        import datetime

        dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        last_date = dt.strftime("%Y-%m-%d")
        clickouse_df = get_install_create_vector_check_rt(last_date)

        clickouse_df["datetime"] = pd.to_datetime(clickouse_df["datetime"], utc=True)
        graylog_df["timestamp"] = pd.to_datetime(graylog_df["timestamp"], utc=True)
        min_graylog_ts = graylog_df["timestamp"].min()
        print("min graylog timestamp: ", min_graylog_ts)
        clickouse_df = clickouse_df[clickouse_df["datetime"] >= min_graylog_ts]

        graylog_df.drop(columns=['message', 'user_id', 'unified_id'], inplace=True)

        result = graylog_df.merge(
            clickouse_df[['payment_account_id']],
            on='payment_account_id',
            how='left',
            indicator=True
        )
        result.to_csv('merged_logs.csv', index=False)

        result_by_merge = (
            result.loc[result['source'] == 'nl14'].groupby('_merge')['payment_account_id']
            .nunique()
        )
        print('losses on nl14 (both - is good, left_only - is bad): ', result_by_merge)

        left_only = result[result['_merge'] == 'left_only']
        left_only = left_only.drop(columns=['_merge'])
        left_only.to_csv('graylog_only.csv', index=False)
        left_only_by_source = (
            left_only.groupby('source')['payment_account_id']
            .nunique()
        )
        print("losses by nodes: ", left_only_by_source)

    return buf.getvalue()


def main():
    st.title("NL14 Install Create Checker")
    st.write("Simple UI to run the install_create comparison between Graylog and ClickHouse.")

    if st.button("Check Android installs"):
        placeholder = st.empty()
        with st.spinner('Running check...'):
            output = run_check(24)
        placeholder.text_area("Output", value=output, height=400)


# run with .venv/bin/python -m streamlit run streamlit_app.py
if __name__ == '__main__':
    main()
