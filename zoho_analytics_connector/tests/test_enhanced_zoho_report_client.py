import sys
import os
import pytest
from typing import MutableMapping
from zoho_analytics_connector.report_client import ReportClient
from zoho_analytics_connector.enhanced_report_client import EnhancedZohoReportClient

class Config:
    LOGINEMAILID = os.getenv('ZOHOANALYTICS_LOGINEMAIL')
    AUTHTOKEN = os.getenv('ZOHOANALYTICS_AUTHTOKEN')
    DATABASENAME = os.getenv('ZOHOANALYTICS_DATABASENAME')
    TABLENAME = "StoreSales"
""" get a token: log in to Zoho Reports, dup a new tab and then paste https://accounts.zoho.com/apiauthtoken/create?SCOPE=ZohoReports/reportsapi"""

class Sample:
    rc = None

    def test(self,opt):

        rc = self.getReportClient()

        if (opt == 6):
            uri = rc.getDBURI(Config.LOGINEMAILID, Config.DATABASENAME)
        else:
            uri = rc.getURI(Config.LOGINEMAILID, Config.DATABASENAME, Config.TABLENAME)
        if (opt == 1):
            self.addSingleRow(rc, uri)
        elif (opt == 2):
            self.updateData(rc, uri)
        elif (opt == 3):
            self.deleteData(rc, uri)
        elif (opt == 4):
            self.importData(rc, uri)
        elif (opt == 5):
            rc.exportData(uri, "CSV", sys.stdout, None, None)
        elif (opt == 6):
            sql = "select Region from " + Config.TABLENAME
            rc.exportDataUsingSQL(uri, "CSV", sys.stdout, sql, None)

    def getReportClient(self):

        if (Config.AUTHTOKEN == ""):
            raise RuntimeError(Exception, "Configure AUTHTOKEN in Config class")

        if (Sample.rc == None):
            Sample.rc = ReportClient(Config.AUTHTOKEN)
        return Sample.rc

    def addSingleRow(self, rc, uri):
        rowData = {"Date": "01 Jan, 2009 00:00:00", "Region": "East", "Product Category": "Samples",
                   "Product": "SampleProduct", "Customer Name": "Sample", "Sales": 2000,
                   "Cost": 2000}
        result = rc.addRow(uri, rowData, None)
        print (result)


    def updateData(self, rc, uri):
        updateInfo = {"Region": "West", "Product": "SampleProduct_2"}
        rc.updateData(uri, updateInfo, "\"Customer Name\"='Sample'", None)

    def deleteData(self, rc, uri):
        rc.deleteData(uri, "\"Customer Name\"='Sample'", None)

    def importData(self, rc, uri):
        try:
            with open('StoreSales.csv', 'r') as f:
                importContent = f.read()
        except Exception as e:
            print("Error Check if file StoreSales.csv exists in the current directory!! ",str(e))
            return
        #import_modes = APPEND / TRUNCATEADD / UPDATEADD
        impResult = rc.import_data(uri, import_mode="TRNCATEADD", import_content=importContent)
        print( "Added Rows :" + str(impResult.successRowCount) + " and Columns :" + str(impResult.selectedColCount))

    def getOption(self):
        print( "\n\nOptions\n 1 - Add Single Row\n 2 - Update Data\n 3 - Delete Data\n 4 - Import Data\n 5 - Export Data\n 6 - Export Data Using SQL")
        print( "\nEnter option : ")
        option = sys.stdin.readline().strip()
        while ((option == "") or (int(option) < 1) or (int(option) > 6)):
            print( "Enter proper option.")
            option = sys.stdin.readline().strip()
        return int(option)



""" move the example code into unit tests, keep the Config class for now"""

@pytest.fixture
def get_report_client()->ReportClient:
    if (Config.AUTHTOKEN == ""):
        raise RuntimeError(Exception, "Please configure AUTHTOKEN in Config class")
    rc = ReportClient(Config.AUTHTOKEN)
    return rc


@pytest.fixture
def get_enhanced_zoho_report_client()->EnhancedZohoReportClient:
    if (Config.AUTHTOKEN == ""):
        raise RuntimeError(Exception, "Please configure AUTHTOKEN in Config class")
    rc = EnhancedZohoReportClient(login_email_id = Config.LOGINEMAILID,
                authtoken=Config.AUTHTOKEN,default_databasename=Config.DATABASENAME)
    return rc

def test_get_database_metadata(get_enhanced_zoho_report_client):
    enhanced_rc = get_enhanced_zoho_report_client
    table_meta_data = enhanced_rc.get_table_metadata()
    assert table_meta_data


def test_data_upload(get_enhanced_zoho_report_client:EnhancedZohoReportClient):
    try:
        with open('StoreSales.csv', 'r') as f:
            import_content = f.read()
    except Exception as e:
        print("Error Check if file StoreSales.csv exists in the current directory!! ", str(e))
        return
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
    impResult = get_enhanced_zoho_report_client.data_upload(import_content=import_content,table_name="sales")
    assert(impResult)


def test_data_download(get_enhanced_zoho_report_client):
    sql="select * from sales"
    result = get_enhanced_zoho_report_client.data_export_using_sql(sql=sql,table_name="sales")
    assert result


def test_make_table():
    pass


