import os

import pytest

from zoho_analytics_connector.enhanced_report_client import EnhancedZohoAnalyticsClient
from zoho_analytics_connector.report_client import ReportClient, ServerError


class Config:
    LOGINEMAILID = os.getenv("ZOHOANALYTICS_LOGINEMAIL")
    REFRESHTOKEN = os.getenv("ZOHOANALYTICS_REFRESHTOKEN")
    AUTHTOKEN = os.getenv("ZOHOANALYTICS_AUTHTOKEN")
    CLIENTID = os.getenv("ZOHOANALYTICS_CLIENTID")
    CLIENTSECRET = os.getenv("ZOHOANALYTICS_CLIENTSECRET")
    DATABASENAME = os.getenv("ZOHOANALYTICS_DATABASENAME")
    SERVER_URL = os.getenv("ZOHO_SERVER_URL")
    REPORT_SERVER_URL = os.getenv("ZOHO_REPORTS_SERVER_URL")

    TABLENAME = "Sales"


# see readme for tips on oauth authentication

# show how to create a ReportClient individually, for the sake of clarity
@pytest.fixture
def get_report_client() -> ReportClient:
    if Config.REFRESHTOKEN == "":
        raise RuntimeError(Exception, "Please configure REFRESHTOKEN in Config class")
    rc = ReportClient(
        token=Config.REFRESHTOKEN,
        clientId=Config.CLIENTID,
        clientSecret=Config.CLIENTSECRET,
    )
    return rc

TEST_OAUTH=True
@pytest.fixture
def enhanced_zoho_analytics_client(zoho_email=None) -> EnhancedZohoAnalyticsClient:
    rc = EnhancedZohoAnalyticsClient(
        login_email_id=zoho_email or Config.LOGINEMAILID,
        token=Config.REFRESHTOKEN if TEST_OAUTH else Config.AUTHTOKEN,
        clientSecret=Config.CLIENTSECRET if TEST_OAUTH else None,
        clientId=Config.CLIENTID if TEST_OAUTH else None,
        default_databasename=Config.DATABASENAME,
        serverURL=Config.SERVER_URL,
        reportServerURL=Config.REPORT_SERVER_URL
    )
    return rc


def test_get_database_metadata(enhanced_zoho_analytics_client):
    enhanced_rc = enhanced_zoho_analytics_client
    table_meta_data = enhanced_rc.get_table_metadata()
    assert table_meta_data


def test_data_upload(enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    try:
        with open("StoreSales.csv", "r") as f:
            import_content = f.read()
    except Exception as e:
        print(
            "Error Check if file StoreSales.csv exists in the current directory!! ",
            str(e),
        )
        return
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
    impResult = enhanced_zoho_analytics_client.data_upload(
        import_content=import_content, table_name="sales"
    )
    assert impResult


def test_data_download(enhanced_zoho_analytics_client):
    sql = "select * from sales"
    result = enhanced_zoho_analytics_client.data_export_using_sql(
        sql=sql, table_name="sales"
    )
    assert len(list(result)) > 0

    # # the table name does not matter
    # # note: if the SQL contains things you need to escape, such as ' characters in a constant you
    # # are passing to IN(...), you have to escape it yourself
    # sql = "select * from animals"
    # result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql, table_name="sales")
    # assert result


zoho_sales_fact_table = {
    "TABLENAME": "sales_fact",
    "COLUMNS": [
        {"COLUMNNAME": "inv_date", "DATATYPE": "DATE"},
        {"COLUMNNAME": "customer", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "sku", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "qty_invoiced", "DATATYPE": "NUMBER"},
        {"COLUMNNAME": "line_total_excluding_tax", "DATATYPE": "NUMBER"},
    ],
}


def test_create_table(enhanced_zoho_analytics_client):
    # is the table already defined?
    try:
        zoho_table_metadata = enhanced_zoho_analytics_client.get_table_metadata()
    except ServerError as e:
        if getattr(e, "message") == "No view present in the workspace.":
            zoho_table_metadata = {}
        else:
            raise
    zoho_tables = set(zoho_table_metadata.keys())

    if "sales_fact" not in zoho_tables:
        enhanced_zoho_analytics_client.create_table(table_design=zoho_sales_fact_table)
    else:
        # get an error, but error handling is not working, the API returns a 400 with no content in the message
        print(f"\nThe table sales_fact exists already; delete it manually to test")
        pytest.fail(
            "This test did not do anything because the table it needs to create exists before the test ran"
        )


def test_delete_rows(enhanced_zoho_analytics_client):
    sql = f"Region IN ('East','West')"
    r = enhanced_zoho_analytics_client.delete_rows(table_name="sales", sql=sql)
    assert r

# needs a COPY_DB_KEY, refer to Zoho documentation
def test_copy_report(enhanced_zoho_analytics_client):
    """ actually, it copies reports,tables and query tables"""

    views = [
        "Animals",
    ]

    target_zoho_email = "tim@growthpath.com.au"
    source_zoho_email = "tim@growthpath.com.au"
    target_zoho_client = enhanced_zoho_analytics_client  #for the test, we have the same client as source and target
    source_dbURI = target_zoho_client.getDBURI(
        dbOwnerName=source_zoho_email, dbName="Super Store Sales"
    )
    r = target_zoho_client.copyReports(
        dbURI=source_dbURI,
        views=",".join(views),
        dbName="DearTest",  #the target workspace
        dbKey=os.getenv("ZOHO_COPY_DB_KEY"),
        config=None,
    )
    print(r)
