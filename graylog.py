import os
from io import StringIO
from urllib import response
from zipfile import Path
import requests
import csv
from dotenv import load_dotenv
import pandas as pd


load_dotenv()

GRAYLOG_URL = os.environ["GRAYLOG_HOST"].rstrip("/")
GRAYLOG_TOKEN = os.environ["GRAYLOG_TOKEN"]


def get_install_create_vector_check_logs(last_hours: int) -> str:
    url = f"{GRAYLOG_URL}/api/search/messages"
    batch_size = 1000
    offset = 0
    all_rows = []

    dfs = []

    while offset < 10000:
        payload = {
            "streams": ["5bdaf7eb491ab904425d70d9"],
            "query": 'message:"install_create_vector_check"',
            "timerange": {
                "type": "relative",
                "range": last_hours * 3600,
            },
            "fields": [
                "timestamp",
                "source",
                "message",
            ],
            "from": offset,
            "size": batch_size,
        }

        headers = {
            "Accept": "text/csv",
            "Content-Type": "application/json",
            "X-Requested-By": "python-script",
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            auth=(GRAYLOG_TOKEN, "token"),
            timeout=60,
        )
        
        print("status:", response.status_code)

            
        csv_text = response.content.decode("utf-8", errors="replace")
        df_chunk = pd.read_csv(StringIO(csv_text))

        if df_chunk.empty:
            break

        dfs.append(df_chunk)        
        print(f"loaded offset={offset}, rows={len(df_chunk)}")

        if len(df_chunk) < batch_size:
            break

        offset += batch_size


    if dfs:
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = pd.DataFrame(columns=["timestamp", "source", "message"])
    df.columns = ["timestamp", "source", "message"]

    df.to_csv("graylog_logs.csv", index=False)

    print(f"Saved to {os.path.abspath('graylog_logs.csv')}")
    return os.path.abspath("graylog_logs.csv")