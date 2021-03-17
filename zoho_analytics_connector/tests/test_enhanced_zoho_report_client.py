import os
import io
import json
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
    assert (not TEST_OAUTH and Config.AUTHTOKEN) or (TEST_OAUTH and Config.REFRESHTOKEN)
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

def get_enhanced_zoho_analytics_client(zoho_email=None) -> EnhancedZohoAnalyticsClient:
    assert (not TEST_OAUTH and Config.AUTHTOKEN) or (TEST_OAUTH and Config.REFRESHTOKEN)
    rc = EnhancedZohoAnalyticsClient(
        login_email_id=zoho_email or Config.LOGINEMAILID,
        token=Config.REFRESHTOKEN if TEST_OAUTH else Config.AUTHTOKEN,
        clientSecret=Config.CLIENTSECRET if TEST_OAUTH else None,
        clientId=Config.CLIENTID if TEST_OAUTH else None,
        default_databasename=Config.DATABASENAME,
        serverURL=Config.SERVER_URL,
        reportServerURL=Config.REPORT_SERVER_URL,
        default_retries=3
    )
    return rc

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

animals_table = {
    "TABLENAME": "animals",
    "COLUMNS": [
        {"COLUMNNAME": "common_name", "DATATYPE": "PLAIN"},
         {"COLUMNNAME": "size", "DATATYPE": "PLAIN" }
    ],
}

def test_create_tables(enhanced_zoho_analytics_client):
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

    if "animals" not in zoho_tables:
        enhanced_zoho_analytics_client.create_table(table_design=animals_table)
    else:
        # get an error, but error handling is not working, the API returns a 400 with no content in the message
        print(f"\nThe table animals table exists already; delete it manually to test")


def test_data_upload():
    enhanced_client = get_enhanced_zoho_analytics_client()
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
    impResult = enhanced_client.data_upload(
        import_content=import_content, table_name="sales"
    )
    assert impResult
    assert impResult.successRowCount == impResult.totalRowCount



def test_get_database_metadata(enhanced_zoho_analytics_client:EnhancedZohoAnalyticsClient):
    table_meta_data = enhanced_zoho_analytics_client.get_table_metadata()
    assert table_meta_data


@pytest.mark.skip
def test_multiple_clients():
    #this does not work
    enhance_client = get_enhanced_zoho_analytics_client()
    enhance_client1 = get_enhanced_zoho_analytics_client()
    table_meta_data = enhance_client1.get_table_metadata()
    assert table_meta_data


def test_addRow():
    #test the standard Zoho ReportClient library function to add two rows
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id, dbName=enhanced_client.default_databasename, tableOrReportName='animals')
    new_row = {'common_name':'Rabbit','size':'small'}
    enhanced_client.addRow( tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'Elephant', 'size': 'large'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)


def test_exportData_csv():
    # Testing a ReportClient function. a binary file object is required to pass in
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri,format='CSV',exportToFileObj=output)
    assert (output.getvalue())

def test_exportData_csv_with_criteria():
    # this test assumes that test_addRow has run
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri,format='CSV',exportToFileObj=output,criteria="size = 'small'")
    returned_data = output.getvalue().decode()
    #assert (output.getvalue())
    assert len(returned_data.split()) == 2  #first row is the headers

def test_exportData_json():
    # Testing a ReportClient function. a binary file object is required to pass in
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    enhanced_client.default_retries = 3
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri,format='JSON',exportToFileObj=output)
    assert (json.loads(output.getvalue()))

def test_deleteData(enhanced_zoho_analytics_client):
    """ This tests the underlying ReportClient function.
    for criteria tips see https://www.zoho.com/analytics/api/?shell#applying-filter-criteria"""
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    criteria = """ 'Rabbit' in "common_name" """
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri,criteria=criteria,retry_countdown=10)
    #assert (row_count==1)

    criteria = """ "common_name" like '%phant' """
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri,criteria=criteria)
    #assert (row_count == 1)

@pytest.mark.skip
def test_rate_limits_data_upload():
    enhanced_client = get_enhanced_zoho_analytics_client()
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
    i = 0
    while i < 100:
        i += 1
        try:
            impResult = enhanced_client.data_upload(
                import_content=import_content, table_name="sales"
            )
            print (f"Import {i} done")
        except Exception as e:
            print (e)


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

# needs a COPY_DB_KEY, refer to Zoho documentation
@pytest.mark.skip
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
