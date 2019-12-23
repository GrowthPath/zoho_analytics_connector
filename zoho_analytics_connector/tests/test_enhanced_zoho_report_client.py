import os
import sys

import pytest

from zoho_analytics_connector.enhanced_report_client import EnhancedZohoAnalyticsClient
# from zoho_analytics_connector.report_client import ReportClient, ServerError
from zoho_analytics_connector.report_client import ReportClient, ServerError


class Config:
    LOGINEMAILID = os.getenv('ZOHOANALYTICS_LOGINEMAIL')
    AUTHTOKEN = os.getenv('ZOHOANALYTICS_AUTHTOKEN')
    DATABASENAME = os.getenv('ZOHOANALYTICS_DATABASENAME')
    TABLENAME = "Sales"


""" get a token: log in to Zoho Reports, dup a new tab and then paste 
https://accounts.zoho.com/apiauthtoken/create?SCOPE=ZohoReports/reportsapi"""


""" Tests for EnhancedZohoAnalyticsClient"""
""" move the example code into unit tests, keep the Config class for now"""


@pytest.fixture
def get_report_client() -> ReportClient:
    if (Config.AUTHTOKEN == ""):
        raise RuntimeError(Exception, "Please configure AUTHTOKEN in Config class")
    rc = ReportClient(Config.AUTHTOKEN)
    return rc


@pytest.fixture
def get_enhanced_zoho_analytics_client() -> EnhancedZohoAnalyticsClient:
    if (Config.AUTHTOKEN == ""):
        raise RuntimeError(Exception, "Please configure AUTHTOKEN in Config class")
    rc = EnhancedZohoAnalyticsClient(login_email_id=Config.LOGINEMAILID,
                                     authtoken=Config.AUTHTOKEN, default_databasename=Config.DATABASENAME)
    return rc


def test_get_database_metadata(get_enhanced_zoho_analytics_client):
    enhanced_rc = get_enhanced_zoho_analytics_client
    table_meta_data = enhanced_rc.get_table_metadata()
    assert table_meta_data


def test_data_upload(get_enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    try:
        with open('StoreSales.csv', 'r') as f:
            import_content = f.read()
    except Exception as e:
        print("Error Check if file StoreSales.csv exists in the current directory!! ", str(e))
        return
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
    impResult = get_enhanced_zoho_analytics_client.data_upload(import_content=import_content, table_name="sales")
    assert (impResult)


def test_data_download(get_enhanced_zoho_analytics_client):
    sql = "select * from sales"
    result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql, table_name="sales")
    assert len(list(result)) > 0

    # # the table name does not matter
    # # note: if the SQL contains things you need to escape, such as ' characters in a constant you
    # # are passing to IN(...), you have to escape it yourself
    # sql = "select * from animals"
    # result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql, table_name="sales")
    # assert result


zoho_sales_fact_table = {
    'TABLENAME': 'sales_fact',
    'COLUMNS': [
        {'COLUMNNAME': 'inv_date', 'DATATYPE': 'DATE'},
        {'COLUMNNAME': 'customer', 'DATATYPE': 'PLAIN'},
        {'COLUMNNAME': 'sku', 'DATATYPE': 'PLAIN'},
        {'COLUMNNAME': 'qty_invoiced', 'DATATYPE': 'NUMBER'},
        {'COLUMNNAME': 'line_total_excluding_tax', 'DATATYPE': 'NUMBER'}]
}


def test_create_table(get_enhanced_zoho_analytics_client):
    # is the table already defined?
    try:
        zoho_table_metadata = get_enhanced_zoho_analytics_client.get_table_metadata()
    except  ServerError as e:
        if getattr(e, 'message') == 'No view present in the workspace.':
            zoho_table_metadata = {}
        else:
            raise
    zoho_tables = set(zoho_table_metadata.keys())

    if "sales_fact" not in zoho_tables:
        get_enhanced_zoho_analytics_client.create_table(table_design=zoho_sales_fact_table)
    else:
        # get an error, but error handling is not working, the API returns a 400 with no content in the message
        print(f"\nThe table sales_fact exists already; delete it manually to test")
        pytest.fail("This test did not do anything because the table it needs to create exists before the test ran")


def test_delete_rows(get_enhanced_zoho_analytics_client):
    sql = f"Region IN ('East','West')"
    r = get_enhanced_zoho_analytics_client.delete_rows(table_name='sales', sql=sql)
    assert r
