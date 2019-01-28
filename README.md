
Zoho Analytics Connector
========================

Zoho's SDK for Zoho Reports is very old, however it is very complete.
This is a version which is Python 3 ready, tested on Python 3.7.
There are not many test cases yet. It is patched to work.

A more convenient wrapper class is in enhanced_report_client.

This is alpha code: what is tested, works. But not much is tested.

The Zoho code still shows its age and my added code was done in a hurry.
I use it mostly for uploading data, and creating and modifying tables, at this point.


Authentication
==============

Authentication is easy.
You log in and visit a URL to gain a token, which does not expire.

Read more here
https://www.zoho.com/analytics/api/#prerequisites


Usage
=====

Zoho's full API is available through the ReportClient API.

EnhancedZohoAnalyticsClient is a higher level layer.

The tests show how to use it:

Setup necessary values (database is the Z.A. Workspace name)

Config class is used in the testcases as a convenience.

    class Config:
        LOGINEMAILID = os.getenv('ZOHOANALYTICS_LOGINEMAIL')
        AUTHTOKEN = os.getenv('ZOHOANALYTICS_AUTHTOKEN')
        DATABASENAME = os.getenv('ZOHOANALYTICS_DATABASENAME')


Make the API instance:

    def get_enhanced_zoho_analytics_client()->EnhancedZohoAnalyticsClient:
        if (Config.AUTHTOKEN == ""):
            raise RuntimeError(Exception, "Please configure AUTHTOKEN in Config class")
        rc = EnhancedZohoAnalyticsClient(login_email_id = Config.LOGINEMAILID,
                                         authtoken=Config.AUTHTOKEN, default_databasename=Config.DATABASENAME)
        return rc

Do some stuff:

    def test_get_database_metadata(get_enhanced_zoho_analytics_client):
        enhanced_rc = get_enhanced_zoho_analytics_client
        table_meta_data = enhanced_rc.get_table_metadata()
        assert table_meta_data


    def test_data_upload(get_enhanced_zoho_analytics_client:EnhancedZohoAnalyticsClient):
        try:
            with open('StoreSales.csv', 'r') as f:
                import_content = f.read()
        except Exception as e:
            print("Error Check if file StoreSales.csv exists in the current directory!! ", str(e))
            return
            # import_modes = APPEND / TRUNCATEADD / UPDATEADD
        impResult = get_enhanced_zoho_analytics_client.data_upload(import_content=import_content,table_name="sales")
        assert(impResult)

        try:
            with open('Animals.csv', 'r') as f:
                import_content2 = f.read()
        except Exception as e:
            print("Error Check if file Animals.csv exists in the current directory!! ", str(e))
            return
        impResult2 = get_enhanced_zoho_analytics_client.data_upload(import_content=import_content2, table_name="animals")
        assert (impResult2)


    def test_data_download(get_enhanced_zoho_analytics_client):
        sql="select * from sales"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result

        #the table name does not matter
        sql="select * from animals"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result
