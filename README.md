
Zoho Analytics Connector
========================

Zoho's SDK for Zoho Reports is very old, however it is very complete.
This is a version which is Python 3 ready, tested on Python 3.7.
There are not many test cases yet. It is patched to work.

A more convenient wrapper class is in enhanced_report_client.

This is alpha code: what is tested, works. But not much is tested.

The Zoho code still shows its age and my added code was done in a hurry.


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
