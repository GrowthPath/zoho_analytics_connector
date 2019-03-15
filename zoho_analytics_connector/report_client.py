""" this is rewritten from some very old code from zoho.
Functions which are modified and tested have PEP8 underscore names
"""
import xml.dom.minidom
import urllib
import urllib3
import json
import requests
from requests.adapters import HTTPAdapter,Retry
from typing import MutableMapping, Optional, Union, List
import logging

logger = logging.getLogger()


def requests_retry_session(
        retries=10,
        backoff_factor=2,
        status_forcelist=(500, 502, 503, 504),
        session=None,
        ) -> requests.Session:
    session = session or requests.Session()
    retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class ReportClient:
    """
    ReportClient provides the python based language binding to the https based api of ZohoReports.
    """

    def __init__(self, authtoken):
        """
        Creates a new C{ReportClient} instance.
        @param authtoken: User's authtoken.
        @type authtoken:string
        """
        # self.iamServerURL="https://accounts.zoho.com"
        self.reportServerURL = "https://analyticsapi.zoho.com"
        self.authtoken = authtoken
        self.requests_session = requests_retry_session()

    def getResp_orig(self, url, httpMethod, payLoad):
        """
        Internal method.(For google app integ).
        """
        try:
            http = urllib3.PoolManager()

            resp = http.request(httpMethod,url, payLoad)
            respObj = ResponseObj(resp)
        except urllib3.exceptions.HTTPError as e:
            respObj = ResponseObj(e)
        return respObj


    def getResp(self, url:str, httpMethod:str, payLoad):
        """
        Internal method.(For google app integ).
        """
        requests_session = self.requests_session or requests_retry_session()
        if httpMethod.upper() == 'POST':
            try:
                resp = requests_session.post(url, data=payLoad,timeout=30)
                respObj = ResponseObj(resp)
            except requests.exceptions.RequestException as e:
                respObj = ResponseObj(e)
            return respObj
        else:
            raise RuntimeError("Unexpected httpMethod in getResp")

    def __sendRequest(self, url, httpMethod, payLoad, action, callBackData):
        respObj = self.getResp(url, httpMethod, payLoad)
        if (respObj.status_code != 200):
            raise ServerError(respObj)
        else:
            return self.handleResponse(respObj, action, callBackData)

    def handle_response_v2(self, response: requests.Response, action: str, callBackData) -> Optional[
        Union[MutableMapping, 'ImportResult', 'ShareInfo', 'PlanInfo']]:
        """ this is a replace for sendRequest: we do the request using requests"""
        if (response.status_code != 200):
            raise ServerError(response)
        else:
            return self.handleResponse(response, action, callBackData)

    def handleResponse(self, response, action, callBackData) -> Optional[
        Union[MutableMapping, 'ImportResult', 'ShareInfo', 'PlanInfo']]:
        """
        Internal method. To be used by classes extending this.
        """
        if ("ADDROW" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            try:
                dict = {}
                cols = dom.getElementsByTagName("column")
                for el in cols:
                    content = ReportClientHelper.getText(el.childNodes).strip()
                    if ("" == content):
                        content = None
                    dict[el.getAttribute("name")] = content
                return dict
            except Exception as inst:
                raise ParseError(resp, "Returned XML format for ADDROW not proper.Could possibly be version mismatch",
                                 inst)
        elif ("UPDATE" == action):
            return None
        elif ("GETCOPYDBKEY" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "copydbkey", response)
        elif ("COPYDB" == action):
            return None
        elif ("DELETE" == action):
            return None
        elif ("EXPORT" == action):
            f = callBackData
            f.write(response.content)
            return None
        elif ("IMPORT" == action):
            return ImportResult(response.content)
        elif ("GETCOPYDBKEY" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "copydbkey", response)
        elif ("GETDATABASENAME" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "dbname", response)
        elif ("GETVIEWNAME" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "viewname", response)
        elif ("GETINFO" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            result = {}
            result['objid'] = ReportClientHelper.getInfo(dom, "objid", response)
            result['dbid'] = ReportClientHelper.getInfo(dom, "dbid", response)
            return result
        elif ("GETVIEWURL" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "viewurl", response)
        elif ("GETEMBEDURL" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "embedurl", response)
        elif ("DATABASEMETADATA" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("GETSHAREINFO" == action):
            return ShareInfo(response.content)
        elif ("GETUSERPLANDETAILS" == action):
            return PlanInfo(response.content)
        elif ("ISDBEXIST" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["isdbexist"]
        elif ("GETUSERS" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("AUTOGENREPORTS" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("HIDECOLUMN" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("SHOWCOLUMN" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("ENABLEDOMAINDB" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("DISABLEDOMAINDB" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("CREATESIMILARVIEWS" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]

    def addRow(self, tableURI, columnValues, config=None):
        """
        Adds a row to the specified table identified by the URI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnValues: Contains the values for the row. The column name(s) are the key.
        @type columnValues:dictionary
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The values of the row.
        @rtype:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([columnValues, config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "ADDROW", "XML")
        return self.__sendRequest(url, "POST", payLoad, "ADDROW", None)

    def deleteData(self, tableURI, criteria=None, config=None):
        """  This has been refactored to use requests.post
        Delete the data in the  specified table identified by the URI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param criteria: The criteria to be applied for deleting. Only rows matching the criteria will be
        updated. Can be C{None}. Incase it is C{None}, then all rows will be deleted.
        @type criteria:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        #payLoad = ReportClientHelper.getAsPayLoad([config], criteria, None)
        payLoad = None # can't put the SQL in the body of the post request, the library is wrong or out of date
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "DELETE", "XML",criteria=criteria)

        r = requests.post(url=url, data=payLoad)
        if (r.status_code != 200):
            raise ServerError(r,criteria=criteria)

        return r  # r.content holds the returned data



    def updateData(self, tableURI, columnValues, criteria, config=None):
        """
        update the data in the  specified table identified by the URI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnValues: Contains the values for the row. The column name(s) are the key.
        @type columnValues:dictionary
        @param criteria: The criteria to be applied for updating. Only rows matching the criteria will be
        updated. Can be C{None}. Incase it is C{None}, then all rows will be updated.
        @type criteria:Optional[string]
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([columnValues, config], criteria, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "UPDATE", "XML")
        self.__sendRequest(url, "POST", payLoad, "UPDATE", None)

    def import_data(self, tableURI: str, import_mode: str,
                    import_content: str,
                    matching_columns:str=None,
                    date_format=None,
                    import_config=None) -> 'ImportResult':
        """ Send data to zoho using a string formatted in CSV style.
        This has been refactored o use requests.post.
        Bulk import data into the table identified by the URI. import_content is a string in csv format (\n separated)
        The first line is column headers.
        Note: the API supports JSON too but it is not implemented here.

        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param import_mode: The type of import.
        Can be one of
         1. APPEND
         2. TRUNCATEADD
         3. UPDATEADD
        See U{Import types<http://zohoreportsapi.wiki.zoho.com/Importing-CSV-File.html>} for more details.
        @type import_mode:string       
        @param import_content: The data in csv format.
        @type import_content:string
        @param import_config: Contains any additional control parameters.
        See U{Import types<http://zohoreportsapi.wiki.zoho.com/Importing-CSV-File.html>} for more details.
        @type import_config:dictionary
        @return: An L{ImportResult} containing the results of the Import
        @rtype:L{ImportResult}
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        date_format = date_format or "yyyy-MM-dd"

        payload = {"ZOHO_AUTO_IDENTIFY": "true",
                   #"ZOHO_COMMENTCHAR":"#",
                   #"ZOHO_DELIMITER":0, #comma
                   #"ZOHO_QUOTED":2, #double quote
                   "ZOHO_ON_IMPORT_ERROR": "ABORT",
                   "ZOHO_CREATE_TABLE": "false", "ZOHO_IMPORT_TYPE": import_mode,
                   "ZOHO_DATE_FORMAT":date_format,
                   "ZOHO_IMPORT_DATA": import_content}


        if matching_columns:
            payload['ZOHO_MATCHING_COLUMNS'] = matching_columns


        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "IMPORT", "XML")

        r = self.requests_session.post(url=url, data=payload,timeout=60)

        return ImportResult(r.content)  # a parser from Zoho

    # def importDataAsString(self, tableURI, importType, importContent, importConfig=None):
    #     """ This is not used anywhere I think?
    #     Bulk import data into the table identified by the URI.
    #     @param tableURI: The URI of the table. See L{getURI<getURI>}.
    #     @type tableURI:string
    #     @param importType: The type of import.
    #     Can be one of
    #      1. APPEND
    #      2. TRUNCATEADD
    #      3. UPDATEADD
    #     See U{Import types<http://zohoreportsapi.wiki.zoho.com/Importing-CSV-File.html>} for more details.
    #     @type importType:string
    #     @param importContent: The data in csv format or json.
    #     @type importContent:string
    #     @param importConfig: Contains any additional control parameters.
    #     See U{Import types<http://zohoreportsapi.wiki.zoho.com/Importing-CSV-File.html>} for more details.
    #     @type importConfig:dictionary
    #     @return: An L{ImportResult} containing the results of the Import.
    #     @rtype:L{ImportResult}
    #     @raise ServerError: If the server has recieved the request but did not process the request
    #     due to some error.
    #     @raise ParseError: If the server has responded but client was not able to parse the response.
    #     """
    #     dict = {"ZOHO_AUTO_IDENTIFY": "true", "ZOHO_ON_IMPORT_ERROR": "ABORT",  #"SETCOLUMNEMPTY"
    #             "ZOHO_ERROR_FORMAT": "JSON",
    #             "ZOHO_DATE_FORMAT": "yyyy-MM-dd",
    #             "ZOHO_CREATE_TABLE": "false", "ZOHO_IMPORT_TYPE": importType,
    #             "ZOHO_IMPORT_DATA": importContent}
    #
    #     payLoad = ReportClientHelper.getAsPayLoad([dict, importConfig], None, None)
    #     url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "IMPORT", "XML")
    #     return self.__sendRequest(url, "POST", payLoad, "IMPORT", None)

    def exportData(self, tableOrReportURI, format, exportToFileObj,
                   criteria:Optional[str]=None, config:Optional[str]=None):
        """
        Export the data in the  specified table identified by the URI.
        @param tableOrReportURI: The URI of the table. See L{getURI<getURI>}.
        @type tableOrReportURI:string
        @param format: The format in which the data is to be exported.
        See U{Supported Export Formats<http://zohoreportsapi.wiki.zoho.com/Export.html>} for
        the supported types.
        @type format:string
        @param exportToFileObj: File (or file like object) to which the exported data is to be written
        @type exportToFileObj:file        
        @param criteria: The criteria to be applied for exporting. Only rows matching the criteria will be
        exported. Can be C{None}. Incase it is C{None}, then all rows will be exported.
        @type criteria:string        
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], criteria, None)
        url = ReportClientHelper.addQueryParams(tableOrReportURI, self.authtoken, "EXPORT", format)
        return self.__sendRequest(url, "POST", payLoad, "EXPORT", exportToFileObj)

    def exportDataUsingSQL(self, tableOrReportURI, format, sql, config=None)->requests.Response:
        """ This has been refactored to use requests.post
        Export the data with the  specified SQL query identified by the URI.
        @param tableOrReportURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type tableOrReportURI:string
        @param format: The format in which the data is to be exported.
        See U{Supported Export Formats<http://zohoreportsapi.wiki.zoho.com/Export.html>} for
        the supported types.
        @type format:string
        @param exportToFileObj: File (or file like object) to which the exported data is to be written
        @type exportToFileObj:file        
        @param sql: The sql whose output need to be exported.
        @type sql:string        
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """

        # this is a bug in Zoho's Python library. The SQL query must be passed as a parameter, not in the body.
        # in the body, it is ignored.
        #payload = ReportClientHelper.getAsPayLoad([config], None, sql)
        payload = None
        """ sql does not need to URL encoded when passed in, but it should be wrapped in quotes I think"""
        # addQueryParams  adds parameters to the URL, not in the POST body but that seems ok for zoho..   url += "&ZOHO_ERROR_FORMAT=XML&ZOHO_ACTION=" + urllib.parse.quote(action)
        # addQueryParams adds: ZOHO_ERROR_FORMAT, ZOHO_OUTPUT_FORMAT
        url = ReportClientHelper.addQueryParams(tableOrReportURI, self.authtoken, "EXPORT", format,sql=sql)  #urlencoding is done in here
        requests_session = self.requests_session or requests_retry_session()
        r = requests_session.post(url=url, data=payload,timeout=30)

        return r  #r.content holds the returned data

    def copyDatabase(self, dbURI, config=None):
        """
        Copy the specified database identified by the URI.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param config: Contains any additional control parameters like ZOHO_DATABASE_NAME.
        @type config:dictionary
        @return: The new database id.
        @rtype: string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "COPYDATABASE", "XML")
        return self.__sendRequest(url, "POST", payLoad, "COPYDB", None)

    def deleteDatabase(self, userURI, databaseName, config=None):
        """
        Delete the specified database.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param databaseName: The name of the database to be deleted.
        @type databaseName:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "DELETEDATABASE", "XML")
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(databaseName)
        return self.__sendRequest(url, "POST", payLoad, "DELETEDATABASE", None)

    def enableDomainDB(self, userUri, dbName, domainName, config=None):
        """
        Enable database for custom domain.
        @param userUri: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userUri:string
        @param dbName: The database name.
        @type dbName:string
        @param domainName: The domain name.
        @type domainName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Domain database status.
        @rtype:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userUri, self.authtoken, "ENABLEDOMAINDB", "JSON")
        url += "&DBNAME=" + urllib.parse.quote(dbName)
        url += "&DOMAINNAME=" + urllib.parse.quote(domainName)
        return self.__sendRequest(url, "POST", payLoad, "ENABLEDOMAINDB", None)

    def disableDomainDB(self, userUri, dbName, domainName, config=None):
        """
        Disable database for custom domain.
        @param userUri: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userUri:string
        @param dbName: The database name.
        @type dbName:string
        @param domainName: The domain name.
        @type domainName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Domain database status.
        @rtype:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userUri, self.authtoken, "DISABLEDOMAINDB", "JSON")
        url += "&DBNAME=" + urllib.parse.quote(dbName)
        url += "&DOMAINNAME=" + urllib.parse.quote(domainName)
        return self.__sendRequest(url, "POST", payLoad, "DISABLEDOMAINDB", None)

    def createTable(self, dbURI, tableDesign, config=None):
        """
        Create a table in the specified database.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param tableDesign: Table structure in JSON format (includes table name, description, folder name, column and lookup details, is system table).
        @type tableDesign:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "CREATETABLE", "JSON")
        #url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote(tableDesign)
        url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote_plus(tableDesign) #smaller URL, fits under limit better

        return self.__sendRequest(url, "POST", payLoad, "CREATETABLE", None)

    def autoGenReports(self, tableURI, source, config=None):
        """
        Generate reports for the particular table.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param source: Source should be column or table.
        @type source:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Auto generate report result.
        @rtype:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "AUTOGENREPORTS", "JSON")
        url += "&ZOHO_SOURCE=" + urllib.parse.quote(source)
        return self.__sendRequest(url, "POST", payLoad, "AUTOGENREPORTS", None)

    def createSimilarViews(self, tableURI, refView, folderName, customFormula, aggFormula, config=None):
        """
        This method is used to create similar views .
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param refView: It contains the refrence view name.
        @type refView:string
        @param folderName: It contains the folder name where the reports to be saved.
        @type folderName:string
        @param customFormula: If its true the reports created with custom formula.
        @type customFormula:bool
        @param aggFormula: If its true the reports created with aggrigate formula.
        @type aggFormula:bool
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Generated reports status.
        @rtype:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "CREATESIMILARVIEWS", "JSON")
        url += "&ZOHO_REFVIEW=" + urllib.parse.quote(refView)
        url += "&ZOHO_FOLDERNAME=" + urllib.parse.quote(folderName)
        url += "&ISCOPYCUSTOMFORMULA=" + urllib.parse.quote("true" if customFormula == True else "false")
        url += "&ISCOPYAGGFORMULA=" + urllib.parse.quote("true" if aggFormula == True else "false")
        return self.__sendRequest(url, "POST", payLoad, "CREATESIMILARVIEWS", None)

    def renameView(self, dbURI, viewName, newViewName, viewDesc="", config=None):
        """
        Rename the specified view with the new name and description.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param viewName: Current name of the view.
        @type viewName:string
        @param newViewName: New name for the view.
        @type newViewName:string
        @param viewDesc: New description for the view.
        @type viewDesc:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "RENAMEVIEW", "XML")
        url += "&ZOHO_VIEWNAME=" + urllib.parse.quote(viewName)
        url += "&ZOHO_NEW_VIEWNAME=" + urllib.parse.quote(newViewName)
        url += "&ZOHO_NEW_VIEWDESC=" + urllib.parse.quote(viewDesc)
        self.__sendRequest(url, "POST", payLoad, "RENAMEVIEW", None)

    def copyReports(self, dbURI, views, dbName, dbKey, config=None):
        """
        The Copy Reports API is used to copy one or more reports from one database to another within the same account or even across user accounts.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param views: This parameter holds the list of view names.
        @type views:string
        @param dbName: The database name where the report's had to be copied.
        @type dbName:string
        @param dbKey: The secret key used for allowing the user to copy the report.
        @type dbKey:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "COPYREPORTS", "XML")
        url += "&ZOHO_VIEWTOCOPY=" + urllib.parse.quote(views)
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        url += "&ZOHO_COPY_DB_KEY=" + urllib.parse.quote(dbKey)
        self.__sendRequest(url, "POST", payLoad, "COPYREPORTS", None)

    def copyFormula(self, tableURI, formula, dbName, dbKey, config=None):
        """
        The Copy Formula API is used to copy one or more formula columns from one table to another within the same database or across databases and even across one user account to another.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param formula: This parameter holds the list of formula names.
        @type formula:string
        @param dbName: The database name where the formula's had to be copied.
        @type dbName:string
        @param dbKey: The secret key used for allowing the user to copy the formula.
        @type dbKey:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "COPYFORMULA", "XML")
        url += "&ZOHO_FORMULATOCOPY=" + urllib.parse.quote(formula)
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        url += "&ZOHO_COPY_DB_KEY=" + urllib.parse.quote(dbKey)
        self.__sendRequest(url, "POST", payLoad, "COPYREPORTS", None)

    def addColumn(self, tableURI, columnName, dataType, config=None):
        """
        Adds a column into Zoho Reports Table.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: The column name to be added into Zoho Reports Table.
        @type columnName:string
        @param dataType: The data type of the column to be added into Zoho Reports Table.
        @type dataType:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "ADDCOLUMN", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        url += "&ZOHO_DATATYPE=" + urllib.parse.quote(dataType)
        return self.__sendRequest(url, "POST", payLoad, "ADDCOLUMN", None)

    def deleteColumn(self, tableURI, columnName, config=None):
        """
        Deletes a column from Zoho Reports Table.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: The column name to be deleted from Zoho Reports Table.
        @type columnName:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "DELETECOLUMN", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        return self.__sendRequest(url, "POST", payLoad, "DELETECOLUMN", None)

    def renameColumn(self, tableURI, oldColumnName, newColumnName, config=None):
        """
        Deactivate the users in the Zoho Reports Account.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param oldColumnName: The column name to be renamed in Zoho Reports Table.
        @type oldColumnName:string
        @param newColumnName: New name for the column.
        @type newColumnName:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "RENAMECOLUMN", "XML")
        url += "&OLDCOLUMNNAME=" + urllib.parse.quote(oldColumnName)
        url += "&NEWCOLUMNNAME=" + urllib.parse.quote(newColumnName)
        return self.__sendRequest(url, "POST", payLoad, "RENAMECOLUMN", None)

    def hideColumn(self, tableURI, columnNames, config=None):
        """
        Hide the columns in the table.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnNames: Contains list of column names.
        @type columnNames:list
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Column status.
        @rtype:list
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "HIDECOLUMN", "JSON")
        for columnName in columnNames:
            url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        return self.__sendRequest(url, "POST", payLoad, "HIDECOLUMN", None)

    def showColumn(self, tableURI, columnNames, config=None):
        """
        Show the columns in the table.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnNames: Contains list of column names.
        @type columnNames:list
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Column status.
        @rtype:list
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "SHOWCOLUMN", "JSON")
        for columnName in columnNames:
            url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        return self.__sendRequest(url, "POST", payLoad, "SHOWCOLUMN", None)

    def addLookup(self, tableURI, columnName, referedTable, referedColumn, onError, config=None):
        """
        Add the lookup for the given column.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: Name of the column (Child column).
        @type columnName:string
        @param referedTable: Name of the referred table (parent table).
        @type referedTable:string
        @param referedColumn: Name of the referred column (parent column).
        @type referedColumn:string
        @param onError: This parameter controls the action to be taken incase there is an error during lookup.
        @type onError:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "ADDLOOKUP", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        url += "&ZOHO_REFERREDTABLE=" + urllib.parse.quote(referedTable)
        url += "&ZOHO_REFERREDCOLUMN=" + urllib.parse.quote(referedColumn)
        url += "&ZOHO_IFERRORONCONVERSION=" + urllib.parse.quote(onError)
        self.__sendRequest(url, "POST", payLoad, "ADDLOOKUP", None)

    def removeLookup(self, tableURI, columnName, config=None):
        """
        Remove the lookup for the given column.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: Name of the column.
        @type columnName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "REMOVELOOKUP", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        self.__sendRequest(url, "POST", payLoad, "REMOVELOOKUP", None)

    def getDatabaseMetadata(self, requestURI, metadata, config=None) -> MutableMapping:
        """
        This method is used to get the meta information about the reports.
        @param requestURI: The URI of the database or table.
        @type requestURI:string
        @param metadata: It specifies the information to be fetched (e.g. ZOHO_CATALOG_LIST, ZOHO_CATALOG_INFO)
        @type metadata:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The metadata of the database.
        @rtype: dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        pay_load = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(requestURI, self.authtoken, "DATABASEMETADATA", "JSON")
        url += "&ZOHO_METADATA=" + urllib.parse.quote(metadata)
        r = requests.post(url=url, data=pay_load)
        return self.handle_response_v2(response=r, action="DATABASEMETADATA", callBackData=None)

    def getDatabaseName(self, userURI, dbid, config=None):
        """
        Get database name for a specified database identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param dbid: The ID of the database.
        @type dbid:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The Database name.
        @rtype: string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "GETDATABASENAME", "XML")
        url += "&DBID=" + urllib.parse.quote(dbid)
        return self.__sendRequest(url, "POST", payLoad, "GETDATABASENAME", None)

    def isDbExist(self, userURI, dbName, config=None):
        """
        Check wheather the database is exist or not.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param dbName: Database name.
        @type dbName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Return wheather the database is exist or not.
        @rtype:string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "ISDBEXIST", "JSON")
        url += "&ZOHO_DB_NAME=" + urllib.parse.quote(dbName)
        return self.__sendRequest(url, "POST", payLoad, "ISDBEXIST", None)

    def getCopyDBKey(self, dbURI, config=None):
        """
        Get copy database key for specified database identified by the URI.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param config: Contains any additional control parameters like ZOHO_REGENERATE_KEY. Can be C{None}.
        @type config:dictionary
        @return: Copy Database key.
        @rtype:string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "GETCOPYDBKEY", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETCOPYDBKEY", None)

    def getViewName(self, userURI, objid, config=None):
        """
        This function returns the name of a view in Zoho Reports.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param objid: The view id (object id).
        @type objid:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The View name.
        @rtype: string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "GETVIEWNAME", "XML")
        url += "&OBJID=" + urllib.parse.quote(objid)
        return self.__sendRequest(url, "POST", payLoad, "GETVIEWNAME", None)

    def getInfo(self, tableURI, config=None):
        """
        This method returns the Database ID (DBID) and View ID (OBJID) of the corresponding Database.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The View-Id (object id) and Database-Id.
        @rtype: dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "GETINFO", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETINFO", None)

    def shareView(self, dbURI, emailIds, views, criteria=None, config=None):
        """
        This method is used to share the views (tables/reports/dashboards) created in Zoho Reports with users.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param emailIds: It contains the owners email-id.
        @type emailIds:string
        @param views: It contains the view names.
        @type views:string
        @param criteria: Set criteria for share. Can be C{None}.
        @type criteria:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], criteria, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "SHARE", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        url += "&ZOHO_VIEWS=" + urllib.parse.quote(views)
        self.__sendRequest(url, "POST", payLoad, "SHARE", None)

    def removeShare(self, dbURI, emailIds, config=None):
        """
        This method is used to remove the shared views (tables/reports/dashboards) in Zoho Reports from the users.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param emailIds: It contains the owners email-id.
        @type emailIds:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "REMOVESHARE", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        self.__sendRequest(url, "POST", payLoad, "REMOVESHARE", None)

    def addDbOwner(self, dbURI, emailIds, config=None):
        """
        This method is used to add new owners to the reports database.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param emailIds: It contains the owners email-id.
        @type emailIds:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "ADDDBOWNER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        self.__sendRequest(url, "POST", payLoad, "ADDDBOWNER", None)

    def removeDbOwner(self, dbURI, emailIds, config=None):
        """
        This method is used to remove the existing owners from the reports database.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param emailIds: It contains the owners email-id.
        @type emailIds:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "REMOVEDBOWNER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        self.__sendRequest(url, "POST", payLoad, "REMOVEDBOWNER", None)

    def getShareInfo(self, dbURI, config=None):
        """
        Get the shared informations.
        @param dbURI: The URI of the database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param config: Contains any additional control parameters like ZOHO_REGENERATE_KEY. Can be C{None}.
        @type config:dictionary
        @return: ShareInfo object.
        @rtype: ShareInfo
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.authtoken, "GETSHAREINFO", "JSON")
        return self.__sendRequest(url, "POST", payLoad, "GETSHAREINFO", None)

    def getViewUrl(self, tableURI, config=None):
        """
        This method returns the URL to access the mentioned view.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The view URI.
        @rtype: string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "GETVIEWURL", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETVIEWURL", None)

    def getEmbedUrl(self, tableURI, criteria=None, config=None):
        """
        This method is used to get the embed URL of the particular table / view. This API is available only for the White Label Administrator. 
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param criteria: Set criteria for url. Can be C{None}.
        @type criteria:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The embed URI.
        @rtype: string
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], criteria, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.authtoken, "GETEMBEDURL", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETEMBEDURL", None)

    def getUsers(self, userURI, config=None):
        """
        Get users list for the user account.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The list of user details.
        @rtype:list
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "GETUSERS", "JSON")
        return self.__sendRequest(url, "POST", payLoad, "GETUSERS", None)

    def addUser(self, userURI, emailIds, config=None):
        """
        Add the users to the Zoho Reports Account.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param emailIds: The email addresses of the users to be added to the Zoho Reports Account separated by comma.
        @type emailIds:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "ADDUSER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "ADDUSER", None)

    def removeUser(self, userURI, emailIds, config=None):
        """
        Remove the users from the Zoho Reports Account.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param emailIds: The email addresses of the users to be removed from the Zoho Reports Account separated by comma.
        @type emailIds:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "REMOVEUSER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "REMOVEUSER", None)

    def activateUser(self, userURI, emailIds, config=None):
        """
        Activate the users in the Zoho Reports Account.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param emailIds: The email addresses of the users to be activated in the Zoho Reports Account separated by comma.
        @type emailIds:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "ACTIVATEUSER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "ACTIVATEUSER", None)

    def deActivateUser(self, userURI, emailIds, config=None):
        """
        Deactivate the users in the Zoho Reports Account.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param emailIds: The email addresses of the users to be deactivated in the Zoho Reports Account separated by comma.
        @type emailIds:string
        @param config: Contains any additional control parameters.
        @type config:dictionary
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "DEACTIVATEUSER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "DEACTIVATEUSER", None)

    def getPlanInfo(self, userURI, config=None):
        """
        Get the plan informations.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters like ZOHO_REGENERATE_KEY. Can be C{None}.
        @type config:dictionary
        @return: PlanInfo object.
        @rtype: PlanInfo
        @raise ServerError: If the server has recieved the request but did not process the request 
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.authtoken, "GETUSERPLANDETAILS", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETUSERPLANDETAILS", None)

    def getUserURI(self, dbOwnerName):
        """
        Returns the URI for the specified user..
        @param dbOwnerName: User email-id of the database.
        @type dbOwnerName:string
        @return: The URI for the specified user. 
        @rtype:string
        """
        url = self.reportServerURL + "/api/" + urllib.parse.quote(dbOwnerName)
        return url

    def getDBURI(self, dbOwnerName, dbName):
        """
        Returns the URI for the specified database.
        @param dbOwnerName: The owner of the database.
        @type dbOwnerName:string
        @param dbName: The name of the database.
        @type dbName:string
        @return: The URI for the specified database.
        @rtype:string
        """
        url = self.reportServerURL + "/api/" + urllib.parse.quote(dbOwnerName)
        url += "/" + self.splCharReplace(urllib.parse.quote(dbName))
        return url

    def getURI(self, dbOwnerName:str, dbName:str, tableOrReportName:str)->str:
        """
        Returns the URI for the specified database table (or report).
        @param dbOwnerName: The owner of the database containing the table (or report).
        @type dbOwnerName:string
        @param dbName: The name of the database containing the table (or report).
        @type dbName:string
        @param tableOrReportName: The  name of the table (or report).
        @type tableOrReportName:string
        @return: The URI for the specified table (or report).
        @rtype:string
        """
        url = self.reportServerURL + "/api/" + urllib.parse.quote(dbOwnerName)
        url += "/" + self.splCharReplace(urllib.parse.quote(dbName)) + "/" + self.splCharReplace(
                urllib.parse.quote(tableOrReportName))

        return url

    def splCharReplace(self, value):
        """
        Internal method for handling special charecters in tale or database name.
        """
        value = value.replace("/", "(/)")
        value = value.replace("%5C", "(//)")
        return value




class ShareInfo:
    """
    It contains the database shared details.
    """

    def __init__(self, response):

        self.response = response
        """
        The unparsed complete response content as sent by the server.
        @type:string
        """

        self.adminMembers = {}
        """
        Owners of the database.
        @type:dictionary
        """

        self.groupMembers = {}
        """
        Group Members of the database.
        @type:dictionary
        """

        self.sharedUsers = []
        """
        Shared Users of the database.
        @type:list
        """

        self.userInfo = {}
        """
        The PermissionInfo for the shared user.
        @type:dictionary
        """

        self.groupInfo = {}
        """
        The PermissionInfo for the groups.
        @type:dictionary
        """

        self.publicInfo = {}
        """
        The PermissionInfo for the public link.
        @type:dictionary
        """

        self.privateInfo = {}
        """
        The PermissionInfo for the private link.
        @type:dictionary
        """

        jsonresult = json.loads(self.response)

        sharelist = jsonresult["response"]["result"]

        userinfo = sharelist["usershareinfo"]
        if (userinfo):
            self.userInfo = self.getKeyInfo(userinfo, "email")

        groupinfo = sharelist["groupshareinfo"]
        if (groupinfo):
            self.groupInfo = self.getKeyInfo(groupinfo, "group")

        publicinfo = sharelist["publicshareinfo"]
        if (publicinfo):
            self.publicInfo = self.getInfo(sharelist["publicshareinfo"])

        privateinfo = sharelist["privatelinkshareinfo"]
        if (privateinfo):
            self.privateInfo = self.getInfo(privateinfo)

        self.adminMembers = sharelist["dbownershareinfo"]["dbowners"]

    def getKeyInfo(self, perminfo, key):

        shareinfo = {}
        i = 0
        for ele in perminfo:
            if ("email" == key):
                info = ele["shareinfo"]["permissions"]
                userid = ele["shareinfo"]["email"]
                self.sharedUsers.append(userid)
            else:
                info = ele["shareinfo"]["permissions"]
                userid = ele["shareinfo"]["groupName"]
                desc = ele["shareinfo"]["desc"]
                gmember = ele["shareinfo"]["groupmembers"]
                member = {}
                member["name"] = userid
                member["desc"] = desc
                member["member"] = gmember
                self.groupMembers[i] = member
                i += 1

            memberlist = {}
            for ele2 in info:
                permlist = {}
                viewname = ele2["perminfo"]["viewname"]
                sharedby = ele2["perminfo"]["sharedby"]
                permissions = ele2["perminfo"]["permission"]
                permlist["sharedby"] = sharedby
                permlist["permissions"] = permissions
                memberlist[viewname] = permlist
            shareinfo[userid] = memberlist
        return shareinfo

    def getInfo(self, perminfo):

        userid = perminfo["email"]
        shareinfo = {}
        memberlist = {}
        for ele in perminfo["permissions"]:
            permlist = {}
            viewname = ele["perminfo"]["viewname"]
            sharedby = ele["perminfo"]["sharedby"]
            permissions = ele["perminfo"]["permission"]
            permlist["sharedby"] = sharedby
            permlist["permissions"] = permissions
            memberlist[viewname] = permlist
        shareinfo[userid] = memberlist
        return shareinfo


class PlanInfo:
    """
    It contains the plan details.
    """

    def __init__(self, response):
        self.response = response
        """
        The unparsed complete response content as sent by the server.
        @type:string
        """

        dom = ReportClientHelper.getAsDOM(response)

        self.plan = ReportClientHelper.getInfo(dom, "plan", response)
        """
        The type of the user plan.
        @type:string
        """

        self.addon = ReportClientHelper.getInfo(dom, "addon", response)
        """
        The addon details.
        @type:string
        """

        self.billingDate = ReportClientHelper.getInfo(dom, "billingDate", response)
        """
        The billing date.
        @type:string
        """

        self.rowsAllowed = int(ReportClientHelper.getInfo(dom, "rowsAllowed", response))
        """
        The total rows allowed to the user.
        @type:int
        """

        self.rowsUsed = int(ReportClientHelper.getInfo(dom, "rowsUsed", response))
        """
        The number of rows used by the user.
        @type:int
        """

        self.trialAvailed = ReportClientHelper.getInfo(dom, "TrialAvailed", response)
        """
        Used to identify the trial pack.
        @type:string
        """

        if ("false" != self.trialAvailed):
            self.trialPlan = ReportClientHelper.getInfo(dom, "TrialPlan", response)
            """
            The trial plan detail.
            @type:string
            """

            self.trialStatus = bool(ReportClientHelper.getInfo(dom, "TrialStatus", response))
            """
            The trial plan status.
            @type:bool
            """

            self.trialEndDate = ReportClientHelper.getInfo(dom, "TrialEndDate", response)
            """
            The end date of the trial plan.
            @type:string
            """


class ServerError(Exception):
    """
    ServerError is thrown if the report server has recieved the request but did not process the
    request due to some error. For example if authorization failure.
    """

    def __init__(self, urlResp,**kwargs):
        self.httpStatusCode = urlResp.status_code  #:The http status code for the request.
        self.errorCode = self.httpStatusCode  # The error code sent by the server.
        self.uri = ""  #: The uri which threw this exception.
        self.action = ""  #:The action to be performed over the resource specified by the uri
        self.message = urlResp.content  #: Returns the message sent by the server.
        self.extra = kwargs

        parseable = False
        contHeader = urlResp.headers["Content-Type"]
        if (contHeader.find("text/xml") > -1):
            self.__parseErrorResponse()

    def __parseErrorResponse(self):
        try:
            dom = xml.dom.minidom.parseString(self.message)
            respEl = dom.getElementsByTagName("response")[0]
            self.uri = respEl.getAttribute("uri")
            self.action = respEl.getAttribute("action")
            self.errorCode = int(ReportClientHelper.getInfo(dom, "code", self.message))
            self.message = ReportClientHelper.getInfo(dom, "message", self.message)
        except Exception as inst:
            print(inst)
            self.parseError = inst

    def __str__(self):
        return repr(self.message)


class ParseError(Exception):
    """
    ParseError is thrown if the server has responded but client was not able to parse the response.
    Possible reasons could be version mismatch.The client might have to be updated to a newer version.
    """

    def __init__(self, responseContent, message, origExcep):
        self.responseContent = responseContent  #: The complete response content as sent by the server.
        self.message = message  #: The message describing the error.
        self.origExcep = origExcep  #: The original exception that occurred during parsing(Can be C{None}).

    def __str__(self):
        return repr(self.message)


class ImportResult:
    """
    ImportResult contains the result of an import operation.
    """

    def __init__(self, response):
        self.response = response
        """
        The unparsed complete response content as sent by the server.
        @type:string
        """
        dom = ReportClientHelper.getAsDOM(response)
        msg = response.decode('utf-8')
        try:
            self.result_code = int(ReportClientHelper.getInfo(dom, "code", response))

        except  ParseError as e:
            #logger.debug(f"Note in import result: could not find result code {msg}")
            self.result_code = 0

        if self.result_code == 6001: #api limit or rows exceeded
            raise RuntimeError(f"API daily limit exceeded: {msg}")
        if self.result_code == 6045:  # api limit or rows exceeded
            raise RuntimeError(f"API rate limit exceeded: {msg}")
        if self.result_code == 7232:
            raise RuntimeError(f"Error in data format: {msg} ")
        try:
            self.totalColCount = int(ReportClientHelper.getInfo(dom, "totalColumnCount", response))
        except ParseError as e:
            logger.debug(f"Error in import result: did not get a good return message: {msg}")
            raise ParseError(msg)
        """
        The total columns that were present in the imported file.
        @type:integer
        """

        self.selectedColCount = int(ReportClientHelper.getInfo(dom, "selectedColumnCount", response))
        """
        The number of columns that were imported.See ZOHO_SELECTED_COLUMNS parameter.
        @type:integer
        """

        self.totalRowCount = int(ReportClientHelper.getInfo(dom, "totalRowCount", response))
        """
        The total row count in the imported file.
        @type:integer
        """

        self.successRowCount = int(ReportClientHelper.getInfo(dom, "successRowCount", response))
        """
        The number of rows that were imported successfully without errors.
        @type:integer
        """

        self.warningCount = int(ReportClientHelper.getInfo(dom, "warnings", response))
        """
        The number of rows that were imported with warnings. Applicable if ZOHO_ON_IMPORT_ERROR
        parameter has been set to SETCOLUMNEMPTY.
        @type:integer
        """

        self.impErrors = ReportClientHelper.getInfo(dom, "importErrors", response)
        """
        The first 100 import errors. Applicable if ZOHO_ON_IMPORT_ERROR parameter is either 
        SKIPROW or  SETCOLUMNEMPTY.  In case of ABORT , L{ServerError <ServerError>} is thrown.
        @type:string
        """

        self.operation = ReportClientHelper.getInfo(dom, "importOperation", response)
        """
        The import operation. Can be either 
         1. B{created} if the specified table has been created. For this ZOHO_CREATE_TABLE parameter
            should have been set to true
         2. B{updated} if the specified table already exists.
        @type:string
        """

        self.dataTypeDict = {}
        """
        Contains the mapping of column name to datatype.
        @type:dictionary
        """

        cols = dom.getElementsByTagName("column")

        self.impCols = []
        """
        Contains the list of columns that were imported. See also L{dataTypeDict<dataTypeDict>}.
        @type:dictionary
        """

        for el in cols:
            content = ReportClientHelper.getText(el.childNodes)
            self.dataTypeDict[content] = el.getAttribute("datatype")
            self.impCols.append(content)


class ResponseObj:
    """
    Internal class.
    """

    def __init__(self, resp:requests.Response):
        """ updated to assume a urllib3 object"""
        self.content = resp.reason #This is used for communication about errors
        self.status_code = resp.status_code
        self.headers = {}
        self.headers = resp.headers


class ReportClientHelper:
    """
    Internal class.
    """

    API_VERSION = "1.0"
    """The api version of zoho reports based on which this library is written. This is a constant."""

    @staticmethod
    def getInfo(dom, elName, response):
        nodeList = dom.getElementsByTagName(elName)
        if (nodeList.length == 0):
            raise ParseError(response, elName + " element is not present in the response", None)
        el = nodeList[0]
        return ReportClientHelper.getText(el.childNodes)

    @staticmethod
    def getText(nodelist):
        txt = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                txt = txt + node.data
        return txt

    @staticmethod
    def getAsDOM(response):
        try:
            dom = xml.dom.minidom.parseString(response)
            return dom
        except Exception as inst:
            raise ParseError(response, "Unable parse the response as xml", inst)

    @staticmethod
    def addQueryParams(url, authtoken, action, exportFormat,sql=None,criteria=None,table_design=None):
        url = ReportClientHelper.checkAndAppendQMark(url)
        if (authtoken == None):
            raise RuntimeError("Provide an AuthToken first")
        url += "&ZOHO_ERROR_FORMAT=JSON&ZOHO_ACTION=" + urllib.parse.quote(action)
        url += "&ZOHO_OUTPUT_FORMAT=" + urllib.parse.quote(exportFormat)
        url += "&authtoken=" + urllib.parse.quote(authtoken) + "&ZOHO_API_VERSION=" + ReportClientHelper.API_VERSION
        if sql:
            url += "&ZOHO_SQLQUERY=" + urllib.parse.quote(sql)
        if criteria:
            url += "&ZOHO_CRITERIA=" + urllib.parse.quote(criteria)
        if table_design:
            #quote_plus seems to work and it makes for a smaller URL avoiding problems with a URL too long
            url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote_plus(table_design)
        return url

    @staticmethod
    def getAsPayLoad(separateDicts, criteria, sql):
        payload = {}
        for i in separateDicts:
            if (i != None):
                payload.update(i)

        if (criteria != None):
            payload["ZOHO_CRITERIA"] = criteria

        if (sql != None):
            payload["ZOHO_SQLQUERY"] = sql

        if (len(payload) != 0):
            payload = urllib.parse.urlencode(payload)
        else:
            payload = None
        return payload

    @staticmethod
    def checkAndAppendQMark(url):
        if (url.find("?") == -1):
            url += "?"
        elif (url[len(url) - 1] != '&'):
            url += "&"
        return url
