
Zoho Analytics Connector
========================

Zoho's SDK for Zoho Reports is very old, however it is very complete.
This is a version which is Python 3 ready, tested on Python 3.8. It has been in production use on several sites for more than 12 months.

A more convenient wrapper class is in enhanced_report_client.
I use it mostly for uploading data, and creating and modifying tables.

AuthTokens are being deprecated, and in some Zoho domains they don't work any longer. 
OAuth support works, see notes below.


Authentication
==============
AuthTokens are deprecated.

OAuth2 notes are below.
When you create EnhancedZohoAnalyticsClient or ReportClient, you need to pass ClientID, ClientSecret and a RefreshToken.
To use AuthToken, pass the AuthToken, and set ClientID and ClientSecret to none.
The test cases give some hints.


For OAuth2:
----------

Visit https://www.zoho.com/analytics/api/#oauth and follow the steps ... in conjunction with the tips here.

Self Clients are an easy start. You choose Self Client when you 'register' (create) a new app.

In the UI, they have purple hexagonal icons. You ae limited to one self-client, so the scope may need to be shared with your other usages amongst Zoho APIs.

The self-client needs to have access rights to the Zoho Analytics accounts, so use as an account on the target organisation with admin rights.

<b>Site to visit</b>

https://api-console.zoho.com/  or .com.au ...

and create a Self Client (at least, to experiment)

Choose the correct domain matching the Zoho Analytics account, e.g. api-console.zoho.com.au 
<p></p>


<b>Tip: The scope for full access</b>

    ZohoReports.fullaccess.all


Now with data gathered (client id, client secret, the code which expires in a few minutes, the scope, execute a POST to

https://accounts.zoho.com/oauth/v2/token?code=

You can do this from terminal with curl:

    curl -d "code=1000.dedaa...&client_id=1000.2TY...&client_secret=b74103c...&grant_type=authorization_code&scope=ZohoReports.fullaccess.all" \
    -X POST https://accounts.zoho.com/oauth/v2/token

and you should get back JSON which looks like this:

    {"access_token":"1000....","refresh_token":"1000.53e...","expires_in_sec":3600,"api_domain":"https://www.zohoapis.com","token_type":"Bearer","expires_in":3600000}

save this somewhere, it is confidential. The refresh token is permanent, it is basically the same as the old authtoken.

NOTE!!! For Australian-hosted Zoho accounts and other regional variations:

The token URL is adapted for the server location. e.g. for Australia, post to https://accounts.zoho.com.au/oauth/v2/token



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

Australian and EU Zoho Servers
------------------------------

The default root of the main server is ```https://accounts.zoho.com```
and the default root of the Analytics API server is ```https://analyticsapi.zoho.com```

You can provide alternatives via the parameters: ```serverURL``` and ```reportServerURL```

Retry exceptions
---------------
in development: calling `enhanced_zoho_analytics_client.data_upload(...)` or `report_client.import_data(...)` can raise one of two exceptions for API limits:
UnrecoverableRateLimitError
RecoverableRateLimitError

Manager retries is a partially implemented experimental feature. `data_upload` uses it.


Do some stuff
-------------

<b>Get table metadata </b>


    def test_get_database_metadata(get_enhanced_zoho_analytics_client):
        enhanced_rc = get_enhanced_zoho_analytics_client
        table_meta_data = enhanced_rc.get_table_metadata()
        assert table_meta_data

<b>Push data </b>

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

 <b>Run SQL</b>. You can join tables. The rows are returned as a DictReader. If you pass ' characters into IN(...) clauses, 
you need to escape them yourself (double ') 

    def test_data_download(get_enhanced_zoho_analytics_client):
        sql="select * from sales"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result

        #the table name does not matter
        sql="select * from animals"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales")
        assert result
        
        
<b>create a table</b>
        
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


