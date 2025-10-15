import io
import json
import os

import pytest
import requests.exceptions

from zoho_analytics_connector.enhanced_report_client import EnhancedZohoAnalyticsClient
from zoho_analytics_connector.report_client import ReportClient, ServerError
from zoho_analytics_connector.typed_dicts import TableView_v2

try:
    from zoho_analytics_connector.private import config
except ModuleNotFoundError:
    pass

class Config:
    LOGINEMAILID = os.getenv("ZOHOANALYTICS_LOGINEMAIL")
    REFRESHTOKEN = os.getenv("ZOHOANALYTICS_REFRESHTOKEN")
    CLIENTID = os.getenv("ZOHOANALYTICS_CLIENTID")
    CLIENTSECRET = os.getenv("ZOHOANALYTICS_CLIENTSECRET")
    DATABASENAME = os.getenv("ZOHOANALYTICS_DATABASENAME")
    # these below are not in private module
    SERVER_URL = os.getenv("ZOHO_SERVER_URL")
    REPORT_SERVER_URL = os.getenv("ZOHO_REPORT_SERVER_URL")
    TABLENAME = "Sales"


# see readme for tips on oauth authentication

# show how to create a ReportClient individually, for the sake of clarity
@pytest.fixture
def get_report_client() -> ReportClient:
    if Config.REFRESHTOKEN == "":
        raise RuntimeError(Exception, "Please configure REFRESHTOKEN in Config class")
    rc = ReportClient(
        refresh_token=Config.REFRESHTOKEN,
        clientId=Config.CLIENTID,
        clientSecret=Config.CLIENTSECRET,
    )
    return rc


TEST_OAUTH = True


@pytest.fixture
def enhanced_zoho_analytics_client(zoho_email=None) -> EnhancedZohoAnalyticsClient:
    assert (not TEST_OAUTH and Config.AUTHTOKEN) or (TEST_OAUTH and Config.REFRESHTOKEN)
    rc = EnhancedZohoAnalyticsClient(
        login_email_id=zoho_email or Config.LOGINEMAILID,
        refresh_token=Config.REFRESHTOKEN if TEST_OAUTH else Config.AUTHTOKEN,
        clientSecret=Config.CLIENTSECRET if TEST_OAUTH else None,
        clientId=Config.CLIENTID if TEST_OAUTH else None,
        default_databasename=Config.DATABASENAME,
        serverURL=Config.SERVER_URL,
        reportServerURL=Config.REPORT_SERVER_URL
    )
    return rc


def get_enhanced_zoho_analytics_client(zoho_email=None, retries=3) -> EnhancedZohoAnalyticsClient:
    assert (not TEST_OAUTH and Config.AUTHTOKEN) or (TEST_OAUTH and Config.REFRESHTOKEN)
    rc = EnhancedZohoAnalyticsClient(
        login_email_id=zoho_email or Config.LOGINEMAILID,
        refresh_token=Config.REFRESHTOKEN if TEST_OAUTH else Config.AUTHTOKEN,
        clientSecret=Config.CLIENTSECRET if TEST_OAUTH else None,
        clientId=Config.CLIENTID if TEST_OAUTH else None,
        default_databasename=Config.DATABASENAME,
        serverURL=Config.SERVER_URL,
        reportServerURL=Config.REPORT_SERVER_URL,
        default_retries=retries
    )
    return rc
#"Date","Region","Product Category","Product","Customer Name","Sales","Cost","Profit"

# see
zoho_sales_table = {
    "TABLENAME": "store_sales",
    "COLUMNS": [
        {"COLUMNNAME": "date", "DATATYPE": "DATE"},
        {"COLUMNNAME": "region", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "product_category", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "product", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "customer_name", "DATATYPE": "PLAIN"},

        {"COLUMNNAME": "sales", "DATATYPE": "DECIMAL_NUMBER"},
        {"COLUMNNAME": "cost", "DATATYPE": "DECIMAL_NUMBER"},
        {"COLUMNNAME": "profit", "DATATYPE": "DECIMAL_NUMBER"},
    ],
}

animals_table = {
    "TABLENAME": "animals",
    "COLUMNS": [
        {"COLUMNNAME": "common_name", "DATATYPE": "PLAIN"},
        {"COLUMNNAME": "size", "DATATYPE": "PLAIN"}
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

    if "store_sales" not in zoho_tables:
        enhanced_zoho_analytics_client.create_table(table_design=zoho_sales_table)
    else:
        # get an error, but error handling is not working, the API returns a 400 with no content in the message
        print("\nThe table store_sales exists already; delete it manually to test")

    if "animals" not in zoho_tables:
        enhanced_zoho_analytics_client.create_table(table_design=animals_table)
    else:
        # get an error, but error handling is not working, the API returns a 400 with no content in the message
        print("\nThe table animals table exists already; delete it manually to test")


def test_data_upload():
    enhanced_client = get_enhanced_zoho_analytics_client()
    try:
        with open("StoreSales.csv", "r") as f:
            import_content = f.read()
    except Exception as e:
        print(
            "Error Check if file StoreSales.csv exists in the current directory; assumption is that the tests directory is the working directory. ",
            str(e),
        )
        return
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
    impResult = enhanced_client.data_upload(
        import_content=import_content, table_name="store_sales",
        import_mode="UPDATEADD",
        matching_columns="date,region,product_category,product,customer_name"
    )
    assert impResult
    assert impResult.successRowCount == impResult.totalRowCount


def test_get_database_metadata(enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    """ this is the way of getting table metadata with the V1 API"""
    table_meta_data = enhanced_zoho_analytics_client.get_table_metadata()
    assert table_meta_data


def test_get_database_metadata_v2(enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    """ this is the way of getting table metadata with the V1 API"""
    table_meta_data_v2 = enhanced_zoho_analytics_client.get_table_metadata_v2()
    assert table_meta_data_v2

def test_get_v2_metadata(enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    metadata = enhanced_zoho_analytics_client.get_orgs_metadata_api_v2()
    assert metadata

def test_get_v2_table_model_data(enhanced_zoho_analytics_client: EnhancedZohoAnalyticsClient):
    workspaces_metadata = enhanced_zoho_analytics_client.get_all_workspaces_metadata_api_v2()
    source_workspace_name = "Cin7Omni"
    for workspace in workspaces_metadata["data"]["ownedWorkspaces"]+ workspaces_metadata["data"]["sharedWorkspaces"]:
        if workspace["workspaceName"] == source_workspace_name:
            workspace_id = workspace["workspaceId"]
            org_id = workspace["orgId"]
            break
    else:
        raise "workspace not found"
    table_catalog = {}
    tables_data = enhanced_zoho_analytics_client.get_views_api_v2(org_id=org_id,workspace_id=workspace_id,view_types=[0])
    for table in tables_data["data"]["views"]:
        view_id = table["viewId"]
        table_details = enhanced_zoho_analytics_client.get_view_details_api_v2(view_id=view_id)
        table = table_details["data"]["views"]

        table_catalog[table["viewName"]] = TableView_v2(columns=table["columns"],tableName=table["viewName"],tableType=table["viewType"],viewID=table["viewId"])
    assert table_catalog


def test_workspace_details(enhanced_zoho_analytics_client:EnhancedZohoAnalyticsClient):
    org_metadata = enhanced_zoho_analytics_client.get_orgs_metadata_api_v2()
    origin_orgid = org_metadata["data"]["orgs"][0]["orgId"]
    dest_orgid = origin_orgid
    workspaces_metadata = enhanced_zoho_analytics_client.get_all_workspaces_metadata_api_v2()
    source_workspace_name = "DearTest"
    for workspace in workspaces_metadata["data"]["ownedWorkspaces"]:
        if workspace["workspaceName"] == source_workspace_name:
            workspace_id = workspace["workspaceId"]
            break
    else:
        raise "workspace not found"
    workspace_details = enhanced_zoho_analytics_client.get_workspace_details_api_v2(workspace_id=workspace_id)
    assert workspace_details

def test_meta_details_v2(enhanced_zoho_analytics_client:EnhancedZohoAnalyticsClient):

    workspaces_metadata = enhanced_zoho_analytics_client.get_all_workspaces_metadata_api_v2()
    target_workspace_name = "Cin7Omni"
    for workspace in workspaces_metadata["data"]["sharedWorkspaces"]:
        if workspace["workspaceName"] == target_workspace_name:
            workspace_id = workspace["workspaceId"]
            org_id = workspace["orgId"]
            break
    else:
        raise "workspace not found"
    meta_detail = enhanced_zoho_analytics_client.get_meta_details_view_api_v2(org_id=org_id,workspace_name="Cin7Omni", view_name="Test")
    assert meta_detail


def test_copy_workspace(enhanced_zoho_analytics_client:EnhancedZohoAnalyticsClient):
    org_metadata = enhanced_zoho_analytics_client.get_orgs_metadata_api_v2()
    origin_orgid = org_metadata["data"]["orgs"][0]["orgId"]
    dest_orgid = origin_orgid
    workspaces_metadata = enhanced_zoho_analytics_client.get_all_workspaces_metadata_api_v2()
    source_workspace_name = "DearTest"
    for workspace in workspaces_metadata["data"]["ownedWorkspaces"]:
        if workspace["workspaceName"] == source_workspace_name:
            workspace_id = workspace["workspaceId"]
            break
    else:
        raise "workspace not found"

    # delete the new destination workspace in case it already exists
    new_workspace_name = "NewWorkspace"
    new_workspace = next((w for w in workspaces_metadata["data"]["ownedWorkspaces"] if w["workspaceName"] == new_workspace_name), None)
    if new_workspace:
        r = enhanced_zoho_analytics_client.delete_workspace_api_v2(workspace_id=new_workspace["workspaceId"],org_id=origin_orgid)

    workspace_secret_key_result = enhanced_zoho_analytics_client.get_workspace_secretkey_api_v2(workspace_id=workspace_id,org_id=origin_orgid)
    workspace_secret_key = workspace_secret_key_result["data"]["workspaceKey"]
    r = enhanced_zoho_analytics_client.copy_workspace_api_v2(new_workspace_name=new_workspace_name,
                                                             workspace_id=workspace_id,
                                                             copy_with_data=False,   # to make it faster
                                                             dest_org_id=dest_orgid,
                                                             source_org_id=origin_orgid,
                                                             workspace_key=workspace_secret_key)




@pytest.mark.skip
def test_multiple_clients():
    # this does not work
    enhance_client = get_enhanced_zoho_analytics_client()
    enhance_client1 = get_enhanced_zoho_analytics_client()
    table_meta_data = enhance_client1.get_table_metadata()
    assert table_meta_data

@pytest.mark.skip
def test_addRow():
    # test the standard Zoho ReportClient library function to add two rows
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename, tableOrReportName='animals')
    new_row = {'common_name': 'Rabbit', 'size': 'small'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'Elephant', 'size': 'large'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)


def test_exportData_csv():
    # Testing a ReportClient function. a binary file object is required to pass in
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri, format='CSV', exportToFileObj=output)
    assert (output.getvalue())


def test_exportData_csv_with_criteria():
    # this test assumes that test_addRow has run
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    criteria = """ "size" in ('small') """
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri, criteria=criteria)
    new_row = {'common_name': 'Rabbit', 'size': 'small'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'Elephant', 'size': 'large'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    output = io.BytesIO()
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri, format='CSV', exportToFileObj=output,
                                   criteria="size = 'small'")
    returned_data = output.getvalue().decode()
    # assert (output.getvalue())
    assert len(returned_data.split()) == 2  # first row is the headers


def test_exportData_json():
    # Testing a ReportClient function. a binary file object is required to pass in
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    enhanced_client.default_retries = 3
    r = enhanced_client.exportData(tableOrReportURI=animals_table_uri, format='JSON', exportToFileObj=output)
    assert (json.loads(output.getvalue()))


def test_add_and_delete_data(enhanced_zoho_analytics_client):
    """ This tests the underlying ReportClient function.
    for criteria tips see https://www.zoho.com/analytics/api/?shell#applying-filter-criteria"""
    enhanced_client = get_enhanced_zoho_analytics_client()
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')

    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename, tableOrReportName='animals')
    new_row = {'common_name': 'Rabbit', 'size': 'small'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'Elephant', 'size': 'large'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'wolf', 'size': 'medium'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)
    new_row = {'common_name': 'leopard', 'size': 'medium'}
    enhanced_client.addRow(tableURI=animals_table_uri, columnValues=new_row)

    criteria = """ 'Rabbit' in "common_name" """
    pre_delete_row_count = enhanced_client.pre_delete_rows(table_name="animals", sql=criteria, retry_countdown=10)
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri, criteria=criteria, retry_countdown=10)
    assert (int(row_count)>=1)
    assert row_count == pre_delete_row_count

    criteria = """ "common_name" like '%phant' """
    pre_delete_row_count = enhanced_client.pre_delete_rows(table_name="animals", sql=criteria, retry_countdown=10)
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri, criteria=criteria)
    assert (int(row_count) >= 1)
    assert row_count == pre_delete_row_count

    criteria = """ "common_name" in ('leopard', 'wolf') """
    pre_delete_row_count = enhanced_client.pre_delete_rows(table_name="animals", sql=criteria, retry_countdown=10)
    row_count = enhanced_client.deleteData(tableURI=animals_table_uri, criteria=criteria)
    assert (int(row_count) >= 1)
    assert row_count == pre_delete_row_count


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
                import_content=import_content, table_name="store_sales"
            )
            print(f"Import {i} done")
        except Exception as e:
            print(e)


class MockResponse:
    # needs to have the sort of things that a Request ersult has
    text = "123"
    response = {}
    @staticmethod
    def json():
        raise ConnectionError


def test_connection_error_data_upload(monkeypatch):
    allowed_retries = 2
    count_retries = 0

    def mock_post(*args, **kwargs):
        nonlocal count_retries
        count_retries += 1
        raise ConnectionError
        # return MockResponse

    enhanced_client = get_enhanced_zoho_analytics_client(retries=allowed_retries)
    monkeypatch.setattr(enhanced_client.requests_session, "post", mock_post)

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

    try:
        impResult = enhanced_client.data_upload(
            import_content=import_content, table_name="store_sales"
        )
    except ConnectionError as e:
        print(e)
        print (f"Retries: {count_retries}")
        assert count_retries == allowed_retries
    except Exception:
        assert False


def test_timeout():
    #
    enhanced_client = get_enhanced_zoho_analytics_client(retries=2)
    enhanced_client.request_timeout = 0.001
    animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                               dbName=enhanced_client.default_databasename,
                                               tableOrReportName='animals')
    output = io.BytesIO()
    with pytest.raises(requests.exceptions.ConnectTimeout):
        r = enhanced_client.exportData(tableOrReportURI=animals_table_uri, format='JSON', exportToFileObj=output)


def test_data_download(enhanced_zoho_analytics_client):
    sql = "select * from store_sales"
    result = enhanced_zoho_analytics_client.data_export_using_sql(
        sql=sql, table_name="store_sales"
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
    target_zoho_client = enhanced_zoho_analytics_client  # for the test, we have the same client as source and target
    source_dbURI = target_zoho_client.getDBURI(
        dbOwnerName=source_zoho_email, dbName="Super Store Sales"
    )
    r = target_zoho_client.copyReports(
        dbURI=source_dbURI,
        views=",".join(views),
        dbName="DearTest",  # the target workspace
        dbKey=os.getenv("ZOHO_COPY_DB_KEY"),
        config=None,
    )
    print(r)
