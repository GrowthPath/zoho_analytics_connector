Zoho Analytics Connector for Python
========================

Zoho's Python SDK for Zoho Reports is old, however it is very complete.
This is a version which is Python 3 ready, tested on Python 3.8 and 3.9 and in fairly substantial production use.

A more convenient wrapper class is in enhanced_report_client. This is based on Zoho's ReportClient but provides some more convenient features.
I use it mostly for uploading data, and creating and modifying tables.

This library uses the Analytics V1 API and as of v.1.4 will phase in v2 API endpoints bit by bit

Authentication
==============
AuthTokens are now retired, replaced with OAuth2.

OAuth2 notes are below.
When you create EnhancedZohoAnalyticsClient or ReportClient, you need to pass ClientID, ClientSecret and a RefreshToken.
The RefreshToken is the equivalent of the old AuthToken.

To use AuthToken (retired authentication method), pass the AuthToken, and set ClientID and ClientSecret to none.
The test cases give some hints.

For OAuth2:
----------

#### Note: Which user?

Only the admin user, the owner, can make the Self Client. Other users, even organisational admins, won't work.

### Choose the correct API Console site

You need to be aware of the Zoho hosting domain, e.g. .com or .com.au etc.

<b>Site to visit</b>

https://api-console.zoho.com/  or 

https://api-console.zoho.com.au

or
...


Self Clients are an easy start to getting authenticated. They are suitable for server-based applications, because there is no user-interaction.

You choose Self Client when you 'register' (create) a new app. A Self Client means that you interactively get a Refresh Token.
OAuth2 is mostly designed for flows where the user interactively approves: the Self Client approach is the equivalent of the old AuthToken, requiring no user action.
However, you need to access the Zoho Analytics account as the admin user.

In the UI, they have purple hexagonal icons. You ae limited to one self-client, so the scope may need to be shared with your other usages amongst Zoho APIs.

So, create a Self Client (at least, to experiment)


<b>Tip: The scope for full access</b>

    ZohoAnalytics.fullaccess.all

I paste this into the Scope Description as well.

Make the 'Time Duration' the maximum: 10 minutes.

Now is a good time to copy the correct curl template from below into a text editor.


Choose "Create"

Now with data gathered (client id, client secret, the code which expires in a few minutes, the scope), execute a POST to

    https://accounts.zoho.com/oauth/v2/token?code=

or for Zoho Australia (.com.au)

    https://accounts.zoho.com.au/oauth/v2/token?code=

or to the URL matching your Zoho data centre.

### Using curl to POST

You can do this from terminal with curl:

    curl -d "code=1000.dedaa...&client_id=1000.2TY...&client_secret=b74103c...&grant_type=authorization_code&scope=ZohoAnalytics.fullaccess.all" \
    -X POST https://accounts.zoho.com/oauth/v2/token

or for Australia

    curl -d "code=1000.dedaa...&client_id=1000.2TY...&client_secret=b74103c...&grant_type=authorization_code&scope=ZohoAnalytics.fullaccess.all" \
     -X POST https://accounts.zoho.com.au/oauth/v2/token

and you should get back JSON which looks like this:

    {"access_token":"1000....","refresh_token":"1000.53e...","expires_in_sec":3600,"api_domain":"https://www.zohoapis.com","token_type":"Bearer","expires_in":3600000}

save this somewhere, it is confidential. The refresh token is permanent, it is basically the same as the old authtoken.

NOTE!!! For Australian-hosted Zoho accounts and other regional variations:

The token URL is adapted for the server location. e.g. for Australia, post to https://accounts.zoho.com.au/oauth/v2/token

Usage
=====

Zoho's full API v1 is available through the ReportClient API. 
Selectively, v2 API endpoints will be added to the ReportClient if they are useful. 

One example of this is get_metadata_api_v2()

Note that for data import and export, my EnhancedReportClient has its own methods, and these are what I use in production so they are much better tested.


    class EnhancedZohoAnalyticsClient(ReportClient)
    
is a higher level layer.

The tests show how to use it:

Setup necessary values (database is the Z.A. Workspace name)

Config class is used in the testcases as a convenience.

    class Config:
        LOGINEMAILID = os.getenv('ZOHOANALYTICS_LOGINEMAIL')
        AUTHTOKEN = os.getenv('ZOHOANALYTICS_AUTHTOKEN')
        DATABASENAME = os.getenv('ZOHOANALYTICS_DATABASENAME')


Make the API instance:

    rc = EnhancedZohoAnalyticsClient(
        login_email_id=Config.LOGINEMAILID,
        token=Config.REFRESHTOKEN if TEST_OAUTH else Config.AUTHTOKEN,
        clientSecret=Config.CLIENTSECRET if TEST_OAUTH else None,
        clientId=Config.CLIENTID if TEST_OAUTH else None,
        default_databasename=Config.DATABASENAME,
        serverURL=Config.SERVER_URL,
        reportServerURL=Config.REPORT_SERVER_URL,
        default_retries=3
    )

Australian and EU Zoho Servers
------------------------------

The default root of the main server is (ServerURL)```https://accounts.zoho.com```
and the default root of the Analytics API server (reportServerURL) is ```https://analyticsapi.zoho.com```

You can provide alternatives via the parameters: ```serverURL``` and ```reportServerURL``` (because you are using a non-US zoho data location)

Retry exceptions
---------------
in development: calling `enhanced_zoho_analytics_client.data_upload(...)` or `report_client.import_data(...)` can raise one of two exceptions for API limits:
UnrecoverableRateLimitError
RecoverableRateLimitError

Managing retries is a beta feature but I am using it in production. It is opt-in except where I was already doing retry.
The retry logic is in 

    def __sendRequest(self, url, httpMethod, payLoad, action, callBackData,retry_countdown=None):

It attempts to differentiate between recoverable and non-recoverable errors. Recoverable errors so far are temporary rate limit errors, errors due to another update running on the same table, and token refresh errors.

It should be enhanced to use smarter retry timing, but first I will see if this works under production loads.

Change in v.1.2.0

You can pass default_retries when creating the client, or you can set it on an existing client.
This will be the retry count if none is specified. This means you can use retries with the 'low-level' report_client methods by setting a retry level at the EnhancedZohoAnalyticsClient level (actually, the attribute is added to ReportClient)

e.g.
    zoho_enhanced_client.default_retries = 5

and then 'low-level' methods such as add_column()  will get the benefit of the retry logic.
Of course, you should be careful to test this.

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
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales",retry_countdown=10)
        assert result
        
You can cache a query too, if you provide a cache object which has the same interface as Django's cache. 
https://docs.djangoproject.com/en/3.1/topics/cache/

this is, the cache object needs to offer cache.set(...) and cache.get(...) as Django does

    from django.core.cache import cache

    def test_data_download(get_enhanced_zoho_analytics_client):
        sql="select * from sales"
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales",cache_object=cache,
            cache_timeout_seconds=600,retry_countdown=10)
        assert result
        
        result = get_enhanced_zoho_analytics_client.data_export_using_sql(sql=sql,table_name="sales",cache_object=cache, cache_timeout_seconds=600)
        assert result

<b>Delete rows</b>

    def test_deleteData(enhanced_zoho_analytics_client):
        """ This tests the underlying ReportClient function.
        for criteria tips see https://www.zoho.com/analytics/api/?shell#applying-filter-criteria"""
        enhanced_client = get_enhanced_zoho_analytics_client()
        animals_table_uri = enhanced_client.getURI(dbOwnerName=enhanced_client.login_email_id,
                                                   dbName=enhanced_client.default_databasename,
                                                   tableOrReportName='animals')
        criteria = """ 'Rabbit' in "common_name" """
        row_count = enhanced_client.deleteData(tableURI=animals_table_uri,criteria=criteria,retry_countdown=10)
        
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


Changes
-------------
1.4.3 Exponential backoff with jitter used for retry
1.4.2 Added reporting_currency to enhanced_reporting_client
1.4.1 Something seems to changed with the UTF encoding returned by the export endpoint. Change decoding to use utf-8-sig 
1.4.0 some adaptation towards new API from Zoho

1.3.6 Documentation updates, test updates. Added a 'pre-delete function' to calculate how many rows should be deleted.
    deleteData returns an int not a string for the number of rows deleted.

1.3.3 - 1.3.5 Handle some more Zoho exceptions

1.3.2 Under heavy concurrent load, an oauth token error was not being caught. Fixed; new token is generated and a retry occurs.

1.3.1 Some small improvements to Zoho error handling

1.3.0 Retry on connection errors. First effort at a test case covering an exception. 
      Simple little helper script to get the auth token from a self-client, get_token.py. This requires PySimpleGUI.

1.2.5 Merged PR with code clean ups, thanks gredondogc

1.2.4 Readme changes

1.2.3 LICENSE file updated to include text relating to the licence

1.2.2 Workaround for error code detection when json decoding fails. Fixed a bug around exception handling

1.2.1 Emoticons are unicode but Analytics raises an error on import. I am now using the emoji library in enhanced_report_client.data_upload to look for emojis and replace them.
so 'Ok to leave at front door 🙂' becomes 'Ok to leave at front door :slightly_smiling_face:'

1.2.0 Specify a default retry count when making report_client or enhanced_report_client
1.1.2 fix issue #2 to fix criteria on export. Added test case.
1.1.1 minor fixes
1.1.0.1 Documentation fixes

1.1.0 Treat "another import is in progress" as a recoverable error (can be retried)
    Move home-made retry logic to low level: report_client.__sendRequest(), and make retry optionally available to the key functions in EnhancedZohoAnalyticsClient. 
    Functions can pass retry_countdown to use retry. The retry handling is coping well under some initial use in high volume production loads.

1.0.4 Documentation improvements

1.0.3 Some slightly better error handling if Zoho returns an empty response
