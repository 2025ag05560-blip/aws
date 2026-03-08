import pytest
import sys
import os

# add project root to path so we can import DataQuality
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root not in sys.path:
    sys.path.insert(0, root)

from DataQuality import check_null_quality


class DummyCursor:
    def __init__(self):
        self.last_query = None

    def execute(self, query):
        self.last_query = query

    def fetchone(self):
        return [123]


def test_check_null_quality_query_and_return():
    cur = DummyCursor()
    result = check_null_quality(cur, schema="Dataq", table="sales_orders", column="order_id")
    assert cur.last_query == 'SELECT COUNT(*) FROM "Dataq"."sales_orders" WHERE "order_id" IS NULL'
    assert result == 123
