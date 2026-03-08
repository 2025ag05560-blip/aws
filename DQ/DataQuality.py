"""
Data Quality Checker for AWS RDS PostgreSQL.

Design principle:
  - All computation (data quality checks) happens in helper functions.
  - Lambda handler is responsible for database persistence.
  - Helper functions accept a cursor and table/column specs, return computed results.
"""

import json
import boto3
import psycopg2
import re
from datetime import datetime

s3_client = boto3.client('s3')
rds_config = {
    'host': 'database-1.cxeuye2ysfk3.ap-southeast-2.rds.amazonaws.com',
    'database': 'DQ',
    'user': 'postgres',
    'password': 'Bitspilani$'
}


# ============ PRIVATE HELPERS ============

def _get_table_data(cursor, schema, table):
    """
    Fetch all rows and column names from a table.

    Returns:
      (columns, rows) where columns is a list of column names in order,
      and rows is a list of tuples from the table.
    """
    # Fetch all data
    query = f'SELECT * FROM "{schema}"."{table}"'
    cursor.execute(query)
    rows = cursor.fetchall()

    # Fetch column names in ordinal order
    cursor.execute(
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{table}' "
        f"ORDER BY ordinal_position"
    )
    columns = [col[0] for col in cursor.fetchall()]

    return columns, rows


def _persist_dq_results(cursor, columns, results, target_schema, target_table):
    """
    Insert data quality results into a target table.

    Args:
      cursor: Database cursor.
      columns: List of original column names.
      results: List of tuples (original_row_values + dq_result + dq_result_desc).
      target_schema: Schema name for the target table.
      target_table: Table name for the target table.

    Returns:
      Number of rows inserted.
    """
    if not results:
        return 0

    column_names = ','.join([f'"{c}"' for c in columns])
    placeholders = ','.join(['%s'] * (len(columns) + 2))
    insert_query = (
        f'INSERT INTO "{target_schema}"."{target_table}" '
        f'({column_names}, dq_result, dq_result_desc) '
        f'VALUES ({placeholders})'
    )
    cursor.executemany(insert_query, results)
    return len(results)


# ============ QUALITY CHECK FUNCTIONS ============

def check_null_quality(cursor, schema, table, column):
    """
    Run a null-count check on a given column.

    Args:
      cursor: Database cursor.
      schema: Schema name.
      table: Table name.
      column: Column name to check.

    Returns:
      Count of NULL values in the column.
    """
    query = f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{column}" IS NULL'
    cursor.execute(query)
    result = cursor.fetchone()[0]
    return result


def check_date_quality(cursor, schema, table, column, date_format='YYYY-MM-DD'):
    """
    Return the count of rows for which `column` cannot be cast to a date.

    Args:
      cursor: Database cursor.
      schema: Schema name.
      table: Table name.
      column: Column name to check.
      date_format: PostgreSQL date format pattern (default: YYYY-MM-DD).

    Returns:
      Count of rows with invalid dates.
    """
    query = (
        f'SELECT COUNT(*) FROM "{schema}"."{table}" '
        f'WHERE to_date("{column}", \'{date_format}\') IS NULL'
    )
    cursor.execute(query)
    return cursor.fetchone()[0]


# ============ COMPUTATION FUNCTIONS (NO WRITES) ============

def compute_null_quality_results(cursor, schema, table, column):
    """
    Compute null-quality results for every row in the source table.

    For each row, checks if the specified column is NULL and appends a pass/fail result.

    Returns:
      (columns, results) where:
        - columns: list of original column names (in order)
        - results: list of tuples (*original_row_values, dq_result, dq_result_desc)
    """
    columns, rows = _get_table_data(cursor, schema, table)
    column_index = columns.index(column)

    results = []
    for row in rows:
        is_null = row[column_index] is None
        dq_result = not is_null
        dq_result_desc = "null check failed" if is_null else "null check passed"
        results.append((*row, dq_result, dq_result_desc))

    return columns, results


def compute_date_quality_results(cursor, schema, table, column, date_format='YYYY-MM-DD'):
    """
    Compute date-quality results for every row in the source table.

    For each row, checks if the specified column value is a valid date matching the format.
    Validates both format (regex) and actual date existence.

    Returns:
      (columns, results) where results are tuples (*original_row_values, dq_result, dq_result_desc)
    """
    columns, rows = _get_table_data(cursor, schema, table)
    column_index = columns.index(column)
    pattern = r'^\d{4}-\d{2}-\d{2}$'  # YYYY-MM-DD format

    results = []
    for row in rows:
        raw = row[column_index]

        if raw is None:
            dq_result = False
            dq_result_desc = "date check failed (null)"
        elif not re.match(pattern, str(raw)):
            dq_result = False
            dq_result_desc = "date check failed (format)"
        else:
            try:
                datetime.strptime(str(raw), "%Y-%m-%d")
                dq_result = True
                dq_result_desc = "date check passed"
            except ValueError:
                dq_result = False
                dq_result_desc = "date check failed (invalid date)"

        results.append((*row, dq_result, dq_result_desc))

    return columns, results


# ============ LAMBDA HANDLER (ORCHESTRATION & WRITES) ============

def lambda_handler(event, context):
    """
    Main Lambda handler: orchestrates data quality checks and persists results.

    Workflow:
      1. Connect to RDS database.
      2. Run NULL quality check (quick count).
      3. Compute NULL quality results for all rows.
      4. Persist NULL results to target table.
      5. Run DATE quality check (quick count).
      6. Compute DATE quality results for all rows.
      7. Persist DATE results to target table.
      8. Commit all changes and close connection.
    """
    try:
        conn = psycopg2.connect(**rds_config)
        cur = conn.cursor()
        print("✓ Connected to RDS database")

        # Load any existing quality rules (informational)
        cur.execute('SELECT * FROM "Dataq".data_quality')
        existing_rules = cur.fetchall()
        print(f"\nExisting quality rules: {len(existing_rules)}")
        for rule in existing_rules:
            print(f"  - {rule}")

        # NULL QUALITY CHECK
        print("\n--- NULL QUALITY CHECK ---")
        null_count = check_null_quality(cur, "Dataq", "sales_orders", "order_id")
        print(f"NULL order_id count: {null_count}")

        cols_null, results_null = compute_null_quality_results(cur, "Dataq", "sales_orders", "order_id")
        rows_written_null = _persist_dq_results(cur, cols_null, results_null, "Dataq", "sales_orders_null_dq")
        print(f"Persisted {rows_written_null} rows to sales_orders_null_dq")

        # DATE QUALITY CHECK
        print("\n--- DATE QUALITY CHECK ---")
        bad_date_count = check_date_quality(cur, "Dataq", "sales_orders", "order_date")
        print(f"Invalid date count: {bad_date_count}")

        cols_date, results_date = compute_date_quality_results(cur, "Dataq", "sales_orders", "order_date")
        rows_written_date = _persist_dq_results(cur, cols_date, results_date, "Dataq", "sales_orders_date_dq")
        print(f"Persisted {rows_written_date} rows to sales_orders_date_dq")

        conn.commit()
        cur.close()
        conn.close()
        print("\n✓ All checks completed successfully")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data quality checks completed',
                'null_check_count': null_count,
                'null_results_written': rows_written_null,
                'date_check_count': bad_date_count,
                'date_results_written': rows_written_date
            })
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Data quality check failed'
            })
        }


# ============ LOCAL TESTING ============

if __name__ == "__main__":
    lambda_handler(None, None)
