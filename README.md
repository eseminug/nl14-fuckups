# nl14-fuckups

## Project Description

A project for identifying and analyzing data loss in the `install_create` event processing pipeline. It compares logs from Graylog with data in ClickHouse to identify discrepancies and determine where event loss occurs.

## Architecture

### Core Components

#### `main.py`
Main script that:
1. Extracts `install_create_vector_check` logs from Graylog for the last N hours
2. Retrieves `install_create` event data from ClickHouse for the previous day
3. Parses Graylog log messages to extract identifiers:
   - `payment_account_id`
   - `user_id`
   - `unified_id`
   - `device_id`
4. Merges data from both sources using `payment_account_id`
5. Identifies data loss (events in Graylog but missing in ClickHouse)
6. Generates reports as CSV files

#### `graylog.py`
Module for Graylog API integration:
- Function `get_install_create_vector_check_logs(last_hours)` - retrieves logs from the last N hours
- Uses batch processing (1000 records per batch)
- Searches for messages containing `install_create_vector_check`
- Filters by stream ID: `5bdaf7eb491ab904425d70d9`
- Returns CSV file with fields: `timestamp`, `source`, `message`
- Saves to `graylog_logs.csv`

#### `clickhouse.py`
Module for ClickHouse integration:
- Function `execute_sql()` - executes SQL queries and returns results as pandas DataFrame
- Function `get_query()` - loads SQL queries from files with parameter interpolation support
- Function `_get_client()` - establishes ClickHouse connection
- Function `_sanitize_sql()` - validates and sanitizes SQL statements
- Error handling with informative messages
- HTTPS connection with SSL verification

#### `queries/install_create.sql`
ClickHouse SQL query that:
- Selects `datetime` and `payment_account_id`
- From table `default.ug_rt_unified_identification_events`
- Filters by date >= yesterday
- Filters for events with type `install_create`
- Excludes zero `payment_account_id` values

## Output

### CSV Files

1. **`graylog_logs.csv`** - raw logs from Graylog
   - Contains all `install_create_vector_check` events for the period

2. **`parsed_graylog_logs.csv`** - processed logs with extracted parameters
   - Extended with fields: `payment_account_id`, `user_id`, `unified_id`, `device_id`

3. **`merged_logs.csv`** - result of merging Graylog and ClickHouse data
   - Contains `_merge` flag indicating match type:
     - `both` - present in both systems ✓
     - `left_only` - in Graylog but not in ClickHouse ✗ (data loss)
     - `right_only` - in ClickHouse but not in Graylog (should not occur)

4. **`graylog_only.csv`** - events present in Graylog but missing in ClickHouse
   - Represents data loss that needs investigation

### Console Output

The script outputs:
- Loss count by source (nodes)
- Statistics by merge type: `both`, `left_only`

## Dependencies

- `pandas` - data processing
- `requests` - HTTP requests to Graylog API
- `clickhouse-connect` - ClickHouse connection
- `python-dotenv` - environment variable loading

## Environment Variables

Required in `.env` file:

```
GRAYLOG_HOST=https://graylog.example.com
GRAYLOG_TOKEN=your_token_here
CLICKHOUSE_HOST=clickhouse.example.com
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=password
```

## Usage

```bash
python main.py
```

The script automatically:
1. Loads logs from Graylog for the last 24 hours
2. Retrieves data from ClickHouse for the previous day
3. Analyzes and compares the data
4. Generates reports as CSV files