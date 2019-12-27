
Zoho Analytics Connector
========================

Zoho's SDK for Zoho Reports is very old, however it is very complete.
This is a version which is Python 3 ready, tested on Python 3.7.
There are not many test cases yet. It is patched to work: 
that is, it's been made Python 3.7 compatible with the least amount of effort.

A more convenient wrapper class is in enhanced_report_client.

This is still Beta, but I have used it extensively in production. Beta because I don't use all of the API, and there are no test cases that cover the entire API.

I use it mostly for uploading data, and creating and modifying tables, at this point.

Zoho updated the 2.7 code with oauth support, as the old tokens are deprecated. I have merged this code into my library, but I have not tested it yet.

Authentication
==============

Authentication is easy.
You log in and visit a URL to gain a token, which does not expire.
This is deprecated in favour of oauth. V 0.4.0 has Zoho's oauth changes, but I haven't tested them yet.

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

#Run SQL. You can join tables. The rows are returned as a DictReader. If you pass ' characters into IN(...) clauses, 
you need to escape them yourself (double ') 

    def test_data_download(get_enhanced_zoho_analytics_client):
        sql="select * from sales"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result

        #the table name does not matter
        sql="select * from animals"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result
        
        
    #create a table
        
    zoho_sales_fact_table = {
        'TABLENAME': 'sales_fact',
        'COLUMNS': [
            {'COLUMNNAME':'inv_date', 'DATATYPE':'DATE'},
            {'COLUMNNAME':'customer', 'DATATYPE':'PLAIN'},
            {'COLUMNNAME':'sku', 'DATATYPE':'PLAIN'},
            {'COLUMNNAME':'qty_invoiced', 'DATATYPE':'NUMBER'},
            {'COLUMNNAME':'line_total_excluding_tax', 'DATATYPE':'NUMBER'}]
        }

    def test_create_table(get_enhanced_zoho_analytics_client):
        #is the table already defined?
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
            #get an error, but error handling is not working, the API returns a 400 with no content in the message
            r = get_enhanced_zoho_analytics_client.create_table(table_design=zoho_sales_fact_table)
            print (r)


