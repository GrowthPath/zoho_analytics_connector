""" this is rewritten from some very old python 2 code from zoho, although I merged their more recent OAuth support.
Functions which are modified and tested have PEP8 underscore names

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
import io
import json
import logging
import os
import random
import re
import time
import urllib
import urllib.parse
import xml.dom.minidom
from typing import MutableMapping, Optional, Union

import requests
from requests.adapters import HTTPAdapter, Retry

from zoho_analytics_connector.zoho_analytics_connector.model_helpers import AnalyticsTableZohoDef_v2, ColumnDef_v2
from zoho_analytics_connector.zoho_analytics_connector.typed_dicts import DataTypeAddColumn, ZohoWorkspacesResponse

logger = logging.getLogger(__name__)


def requests_retry_session(
        retries=5,
        backoff_factor=2,
        status_forcelist=(500, 502, 503, 504),
        session=None,
) -> requests.Session:
    session = session or requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Represents a single workspace entry (owned or shared)


# Represents the 'data' part of the response, containing lists of workspaces


# Represents the overall structure of the API response


class ReportClient:
    """
     ReportClient provides the python based language binding to the https based API of Zoho Analytics.
     @note: Authentication via authtoken is deprecated, use OAuth. kindly send parameter as ReportClient(token,clientId,clientSecret).
     """

    # Define a default file name for token persistence.
    token_file = "access_token.json"

    isOAuth = False
    request_timeout = 60

    def __init__(self, refresh_token, clientId=None, clientSecret=None,
                 serverURL=None, reportServerURL=None, default_retries=0, access_token=None):
        """
        Initializes a ReportClient instance.
        """
        self.iamServerURL = serverURL or "https://accounts.zoho.com"
        self.reportServerURL = reportServerURL or "https://analyticsapi.zoho.com"
        self.requests_session = requests_retry_session(retries=default_retries)
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.refresh_token = refresh_token
        self.token_timestamp = time.time()  # use current time as a safe default
        self.default_retries = default_retries

        if clientId is None and clientSecret is None:
            # not using OAuth2, so use the refresh_token as the access token
            self.__access_token = refresh_token
        else:
            # If an access token is provided directly, use it.
            # Otherwise, try to load an existing persisted token.
            self.__access_token = access_token or self.load_token()
            ReportClient.isOAuth = True

    @property
    def access_token(self):
        """
        Returns a valid access token. If the current token is expired or None, it will refresh it.
        """
        # Consider token expired if more than 50 minutes old or never set.
        if ReportClient.isOAuth and (time.time() - self.token_timestamp > 50 * 60 or self.__access_token is None):
            logger.debug("Refreshing Zoho Analytics OAuth token")
            self.getOAuthToken()
        return self.__access_token

    @access_token.setter
    def access_token(self, token):
        self.__access_token = token
        self.token_timestamp = time.time()
        # Persist the token whenever it is updated.
        self.persist_token(token)

    def persist_token(self, token: str):
        """
        Default implementation of token persistence.
        Saves the access token and token timestamp as JSON to a local file.
        Subclasses may override this method to provide a different persistence mechanism.
        """
        data = {
            "access_token": token,
            "token_timestamp": self.token_timestamp
        }
        try:
            with open(self.token_file, "w") as out_file:
                json.dump(data, out_file)
            logger.debug("Access token persisted to %s", self.token_file)
        except Exception as e:
            logger.error("Error persisting the token: %s", e)

    def load_token(self) -> str:
        """
        Default implementation of token loading.
        Loads the access token and token timestamp from a local JSON file.
        Subclasses may override this method to provide a different persistence mechanism.
        Returns:
            The access token if found; otherwise, returns None.
        """
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as in_file:
                    data = json.load(in_file)
                    self.token_timestamp = data.get("token_timestamp", time.time())
                    logger.debug("Access token loaded from %s", self.token_file)
                    return data.get("access_token")
            except Exception as e:
                logger.error("Error loading the token: %s", e)
        return None

    def getOAuthToken(self) -> str:
        """
        Internal method for fetching a new OAuth token.
        Should only be invoked when needed. After a successful fetch, it updates
        the instance's token, timestamp, and calls the persistence mechanism.
        Returns:
            The new access token as a string.
        Raises:
            ServerError: If the request to refresh the token fails.
            ValueError: If the access token cannot be extracted from the response.
        """
        auth_dict = {
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        accUrl = self.iamServerURL + "/oauth/v2/token"
        respObj = self.getResp(accUrl, "POST", auth_dict, add_token=False)
        if respObj.status_code != 200:
            raise ServerError(respObj)
        resp = respObj.response.json()  # assuming respObj.response supports .json()
        if "access_token" in resp:
            new_token = resp["access_token"]
            self.__access_token = new_token
            self.token_timestamp = time.time()
            self.persist_token(new_token)
            return new_token
        raise ValueError("Error while getting OAuth access token", resp)

    def getResp(self, url: str, httpMethod: str, payLoad, add_token=True, extra_headers=None, **kwargs):
        """
        Internal method. For GET, payLoad is params; for POST, it's data; for DELETE, it may be data or params.
        """
        requests_session = self.requests_session or requests_retry_session()

        # Build common headers
        headers = {}
        if add_token and ReportClient.isOAuth and hasattr(self, 'access_token'):
            headers["Authorization"] = "Zoho-oauthtoken " + self.access_token
        headers['User-Agent'] = "ZohoAnalytics Python GrowthPath Library"

        if extra_headers:
            headers = {**headers, **extra_headers}

        # Process based on HTTP method
        if httpMethod.upper() == 'POST':
            try:
                resp = requests_session.post(url, data=payLoad, headers=headers, timeout=self.request_timeout, **kwargs)
                if 'invalid client' in resp.text:
                    raise requests.exceptions.RequestException("Invalid Client")
                respObj = ResponseObj(resp)
            except requests.exceptions.RequestException as e:
                logger.exception(f"{e=}")
                raise e
            return respObj

        elif httpMethod.upper() == 'GET':
            try:
                resp = requests_session.get(url, params=payLoad, headers=headers, timeout=self.request_timeout,
                                            **kwargs)
                if 'invalid client' in resp.text:
                    raise requests.exceptions.RequestException("Invalid Client")
                respObj = ResponseObj(resp)
            except requests.exceptions.RequestException as e:
                logger.exception(f"{e=}")
                raise e
            return respObj

        elif httpMethod.upper() == 'DELETE':
            try:
                # Depending on the API, a DELETE request might accept data or params.
                # Here we assume payLoad can be sent as either 'data' or 'params'. Adjust as required.
                resp = requests_session.delete(url, data=payLoad, headers=headers, timeout=self.request_timeout,
                                               **kwargs)
                if 'invalid client' in resp.text:
                    raise requests.exceptions.RequestException("Invalid Client")
                respObj = ResponseObj(resp)
            except requests.exceptions.RequestException as e:
                logger.exception(f"{e=}")
                raise e
            return respObj

        else:
            raise RuntimeError(f"Unexpected httpMethod in getResp, expected POST, GET, or DELETE but got {httpMethod}")

    def __sendRequest(self, url, httpMethod, payLoad, action, callBackData=None, retry_countdown: int = None,
                      extra_headers=None, **keywords):
        code = ""
        if not retry_countdown:
            retry_countdown = self.default_retries or 1
        init_retry_countdown = retry_countdown
        last_exception = None
        last_respObj = None
        while retry_countdown > 0:
            retry_countdown -= 1
            try:
                respObj = self.getResp(url, httpMethod, payLoad, extra_headers=extra_headers, **keywords)
                last_respObj = respObj
                last_exception = None
            except Exception as e:
                last_exception = e
                last_respObj = None
                logger.exception(f" getResp exception in __sendRequest, {retry_countdown}, {e}")  # connection error
                if retry_countdown <= 0:
                    raise e
                else:
                    sleep_time = min((3 * (2 ** (10 - retry_countdown))) + random.random(),
                                     60)  # Add jitter and cap max delay at 60 seconds

                    time.sleep(sleep_time)
                    continue

            if (respObj.status_code in [200, ]):
                return self.handleResponse(respObj, action, callBackData)
            elif (respObj.status_code in [204, ]):  # successful but nothing to return
                return self.handleResponse(respObj, action, callBackData)
            elif (respObj.status_code in [400, 403]):
                # 400 errors may be an API limit error, which are handled by the result parsing
                try:
                    try:
                        # j = respObj.response.json(strict=False) #getting decode errors in this and they don't make sense
                        j = json.loads(respObj.response.text, strict=False)
                        code = j['response']['error']['code']
                    except json.JSONDecodeError as e:
                        logger.error(f"API caused a JSONDecodeError for {respObj.response.text} ")
                        code = None
                    if not code:
                        m = re.search(r'"code":(\d+)', respObj.response.text)
                        if m:
                            code = int(m.group(1))
                        else:
                            code = -1
                            logger.error(f"could not find error code in {respObj.response.text} ")
                            raise ServerError(urlResp=respObj, zoho_error_code=code)
                            # time.sleep(min(10 - retry_countdown, 1) * 10)
                            # continue

                    logger.debug(f"API returned a 400 result and an error code: {code} ")
                    if code in [6045, ]:
                        logger.error(
                            f"Zoho API Recoverable rate limit (rate limit exceeded); there are {retry_countdown + 1} retries left")
                        if retry_countdown < 0:
                            logger.error(
                                f"Zoho API Recoverable error (rate limit exceeded), but exhausted retries")
                            raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                        else:
                            time.sleep(min(10 - retry_countdown, 1) * 10)
                            continue
                    elif code in [6001, ]:
                        logger.error(
                            f"6001 error, rows in Zoho plan exceeded {respObj.response.text}")
                        raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                    elif code in [6043, ]:
                        logger.error(
                            f"6043 error, daily API limit in Zoho plan exceeded {respObj.response.text}")
                        raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7103, ]:
                        logger.error(
                            f"7103 error, workspace not found (check authentication) {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7107, ]:
                        logger.error(
                            f"7107 error, column does not exist:  {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7111, ]:
                        logger.error(
                            f"71111 error, table already exists:  {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7179, ]:
                        logger.error(
                            f"7179 error, workspace reports no view present. Initialise with a dummy table {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7183, ]:
                        logger.error(
                            f"7183 error, lookup column types don't match {respObj.response.text}")
                    elif code in [7184, ]:
                        logger.error(
                            f"7184 error, cyclic lookup detected {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7198, ]:
                        logger.error(
                            f"7198 error, table design changes still in progress {respObj.response.text}  there are {retry_countdown + 1} retries left")

                        if retry_countdown < 0:
                            logger.error(
                                f"Zoho API Recoverable error (table maintenance ongoing), but exhausted retries")
                            raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                        else:
                            time.sleep(min(10 - retry_countdown, 1) * 10)
                            continue
                    elif code in [7232, ]:
                        logger.error(
                            f"7232 error,an invalid value has been provided according to the column's data type) {respObj.response.text=} ")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7280, ]:
                        logger.error(
                            f"7280 error, relating to schema errors, return immediately {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7301, ]:
                        logger.error(
                            f"7301 error, relating to permission errors, return immediately {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7378, ]:
                        logger.error(f"7378 Possible attempt to remove a lookup when no such lookup exists {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7389, ]:
                        logger.error(f"7389 Error from zoho Organisation does not exist {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7403, ]:
                        logger.error(f"7403 SQL Parsing Error {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [7407, ]:
                        logger.error(f"7403 SQL Unknown column {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [8504, ]:
                        logger.error(f"8594 Teh ZOHO_REFERREDTABLE argument when calling ADDLOOKUP was wrong {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [8540, ]:
                        logger.error(f"8540 Error, token has incorrect scope {respObj.response.text}")
                        raise ServerError(urlResp=respObj, zoho_error_code=code)
                    elif code in [8535, ]:  # invalid oauth token
                        try:
                            self.getOAuthToken()
                        except:
                            pass
                        logger.error(f"Zoho API Recoverable error encountered (invalid oauth token), will retry")
                        if retry_countdown < 0:
                            logger.error(
                                f"Zoho API Recoverable error (invalid oauth token) exhausted retries")
                            raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                        else:
                            time.sleep(min(10 - retry_countdown, 1) * 10)
                            continue
                    elif code in [8509, ]:  # parameter does not match accepted input pattern
                        logger.error(
                            f"Error 8509 encountered, something is wrong with the data format, no retry is attempted")
                        raise BadDataError(respObj, zoho_error_code=code)
                    elif code in [10001, ]:  # 10001 is "Another import is in progress, so we can try this again"
                        logger.error(
                            f"Zoho API Recoverable error encountered (Another import is in progress), will retry")
                        if retry_countdown < 0:
                            logger.error(
                                f"Zoho API Recoverable error (Another import is in progress) but exhausted retries")
                            raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code,
                                                              message="Zoho error: Another import is in progress")
                        else:
                            time.sleep(min(10 - retry_countdown, 1) * 10)
                            continue

                    else:
                        # raise ServerError(respObj,zoho_error_code=code)
                        msg = f"Unexpected status code {code=}, will attempt retry"
                        try:
                            msg += respObj.response.text
                        except Exception:
                            pass
                        logger.exception(msg)
                        time.sleep(min(10 - retry_countdown, 1) * 10)
                        continue
                except (RecoverableRateLimitError, UnrecoverableRateLimitError, BadDataError):
                    raise
                except ServerError as e:
                    logger.error(f"ServerError raised on _sendRequest.  {url=} {payLoad=} {action=} ")
                    import_data = payLoad.get("ZOHO_IMPORT_DATA") if payLoad else None
                    if import_data:
                        logger.error(
                            f"Import data, a csv file as a string. Row 1 is header, col 0 is first col (id): {import_data} ")
                    raise ServerError(respObj, zoho_error_code=code, payload=payLoad)
            elif (respObj.status_code in [401, ]):
                try:
                    # j = respObj.response.json(strict=False) #getting decode errors in this and they don't make sense
                    j = json.loads(respObj.response.text, strict=False)
                    code = j['response']['error']['code']
                except json.JSONDecodeError as e:
                    logger.error(f"API caused a JSONDecodeError for {respObj.response.text} ")
                    code = None
                logger.debug(f"API returned a 401 result and an error code: {code} ")
                if code in [8535, ]:  # invalid oauth token
                    try:
                        self.getOAuthToken()
                    except:
                        pass
                    logger.error(f"Zoho API Recoverable error encountered (invalid oauth token), will retry")
                    if retry_countdown < 0:
                        logger.error(
                            f"Zoho API Recoverable error (invalid oauth token) exhausted retries")
                        raise UnrecoverableRateLimitError(urlResp=respObj, zoho_error_code=code)
                    else:
                        time.sleep(min(10 - retry_countdown, 1) * 10)
                        continue
            elif (respObj.status_code in [414, ]):
                msg = f"HTTP response 414 was encountered (URI too large), no retry is attempted. {respObj.response.text} URL for {httpMethod=} {url=} {payLoad=}"
                logger.error(msg)
                raise BadDataError(respObj, zoho_error_code=None)

            elif (respObj.status_code in [500, ]):
                code = respObj.response.status_code
                if ":7005" in respObj.response.text:
                    logger.error(
                        f"Error 7005 encountered ('unexpected error'), no retry is attempted. {respObj.response.text}")
                    raise BadDataError(respObj, zoho_error_code=code)
            else:
                try:
                    response_text = respObj.response.text
                except Exception as e:
                    response_text = "unreadable response text"
                msg = f"Unexpected status code in from __sendRequest. Server response code is {respObj.status_code=} {response_text=}.  {url=}, {httpMethod=}, {payLoad=}, {action=} Retry attempts will be made..."
                logger.exception(msg)
                time.sleep(min(10 - retry_countdown, 1) * 10)
                continue
        # fell off while loop
        error_details = ""
        if last_exception:
            error_details = f"Last error was an exception: {last_exception!r}"
        elif last_respObj:
            response_text = ""
            try:
                response_text = last_respObj.response.text
            except Exception:
                response_text = "could not get response text."
            error_details = f"Last error response status: {last_respObj.status_code}, text: {response_text}"

        display_payload = payLoad
        if isinstance(payLoad, dict) and 'ZOHO_IMPORT_DATA' in payLoad:
            display_payload = payLoad.copy()
            data = display_payload.get('ZOHO_IMPORT_DATA', "")
            if isinstance(data, str) and len(data) > 500:
                display_payload['ZOHO_IMPORT_DATA'] = data[:500] + '... (truncated)'

        raise RuntimeError(
            f"After starting with {init_retry_countdown} retries allowed, there are now no more retries left in __sendRequest. "
            f"{error_details}. {url=}, {httpMethod=}, payLoad={display_payload}, {action=}"
        )

    def invalidOAUTH(self, respObj):
        """
        Internal method to check whether accesstoken expires or not.
        """
        if (respObj.status_code != 200):
            try:
                dom = ReportClientHelper.getAsDOM(respObj.content)
                err_code = dom.getElementsByTagName("code")
                err_code = ReportClientHelper.getText(err_code[0].childNodes).strip()
                return err_code == "8535"
            except Exception:
                return False

        return False

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
        Internal method. To be used by classes extending this. To phase in V2 api,
        set action  to be None or "API_V2"
        """
        if not action or action == "API_V2":
            resp = response.content
            resp_json = json.loads(resp) if resp else {}  # 204 responses are empty
            return resp_json
        elif ("ADDROW" == action):
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
        elif ("DELETE" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["deletedrows"]
        elif ("UPDATE" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["updatedRows"]
        elif ("IMPORT" == action):
            return ImportResult(response.content)
        elif ("EXPORT" == action):
            f = callBackData
            f.write(response.content)
            return None
        elif ("COPYDB" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["dbid"]
        elif ("AUTOGENREPORTS" == action or "CREATESIMILARVIEWS" == action):
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
        elif ("DATABASEMETADATA" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("GETDATABASENAME" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "dbname", response)
        elif ("GETDATABASEID" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "dbid", response)
        elif ("ISDBEXIST" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["isdbexist"]
        elif ("ISVIEWEXIST" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["isviewexist"]
        elif ("ISCOLUMNEXIST" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]["iscolumnexist"]
        elif ("GETCOPYDBKEY" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "copydbkey", response)
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
        elif ("GETSHAREINFO" == action):
            return ShareInfo(response.content)
        elif ("GETVIEWURL" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "viewurl", response)
        elif ("GETEMBEDURL" == action):
            resp = response.content
            dom = ReportClientHelper.getAsDOM(resp)
            return ReportClientHelper.getInfo(dom, "embedurl", response)
        elif ("GETUSERS" == action):
            resp = response.content
            resp = json.loads(resp)
            return resp["response"]["result"]
        elif ("GETUSERPLANDETAILS" == action):
            return PlanInfo(response.content)
        elif ("GETDASHBOARDS" == action):
            resp = response.content
            resp = (json.loads(resp))
            return (resp["response"]["result"]["dashboards"])
        elif ("RECENTITEMS" == action):
            resp = response.content
            resp = (json.loads(resp))
            return (resp["response"]["result"]["recentviews"])
        elif (
                "GETVIEWINFO" == action or "MYWORKSPACELIST" == action or "SHAREDWORKSPACELIST" == action or "VIEWLIST" == action or "FOLDERLIST" == action):
            resp = response.content
            resp = (json.loads(resp))
            return (resp["response"]["result"])
        elif ("SAVEAS" == action):
            resp = response.content
            resp = (json.loads(resp))
            return (resp["response"]["result"]["message"])

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
        # payLoad = ReportClientHelper.getAsPayLoad([columnValues, config], None, None)
        # url = ReportClientHelper.addQueryParams(tableURI, self.token, "ADDROW", "XML")
        # url += "&" + payLoad
        # return self.__sendRequest(url, "POST", payLoad=None, action="ADDROW", callBackData=None)

        payLoad = ReportClientHelper.getAsPayLoad([columnValues, config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "ADDROW", "XML")
        return self.__sendRequest(url, "POST", payLoad, "ADDROW", None)

    def deleteData(self, tableURI, criteria=None, config=None, retry_countdown=0) -> int:
        """  This has been refactored to use requests.post.
        Returns the number of rows deleted
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
        # payLoad = ReportClientHelper.getAsPayLoad([config], criteria, None)
        payload = None  # can't put the SQL in the body of the post request, the library is wrong or out of date
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "DELETE", "JSON", criteria=criteria)
        r = self.__sendRequest(url=url, httpMethod="POST", payLoad=payload, action="DELETE", callBackData=None,
                               retry_countdown=retry_countdown)
        return int(r)

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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "UPDATE", "JSON")
        return self.__sendRequest(url, "POST", payLoad, "UPDATE", None)

    def importData(self, tableURI, importType, importContent, autoIdentify="TRUE", onError="ABORT", importConfig=None):
        """
        Bulk import data into the table identified by the URI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param importType: The type of import.
        Can be one of
         1. APPEND
         2. TRUNCATEADD
         3. UPDATEADD
        See U{Import types<https://www.zoho.com/analytics/api/#import-data>} for more details.
        @type importType:string
        @param importContent: The data in csv format.
        @type importContent:string
        @param autoIdentify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
        @type autoIdentify:string
        @param onError: This parameter controls the action to be taken In-case there is an error during import.
        @type onError:string
        @param importConfig: Contains any additional control parameters.
        See U{Import types<https://www.zoho.com/analytics/api/#import-data>} for more details.
        @type importConfig:dictionary
        @return: An L{ImportResult} containing the results of the Import
        @rtype:L{ImportResult}
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        if (importConfig == None):
            importConfig = {}
        importConfig['ZOHO_IMPORT_TYPE'] = importType
        importConfig["ZOHO_ON_IMPORT_ERROR"] = onError
        importConfig["ZOHO_AUTO_IDENTIFY"] = autoIdentify

        if not ("ZOHO_CREATE_TABLE" in importConfig):
            importConfig["ZOHO_CREATE_TABLE"] = 'false'

        files = {"ZOHO_FILE": ("file", importContent, 'multipart/form-data')}
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "IMPORT", "XML")

        headers = {}
        # To set access token for the first time when an instance is created.
        if ReportClient.isOAuth:
            if self.accesstoken == None:
                self.accesstoken = self.getOAuthToken()
            headers = {"Authorization": "Zoho-oauthtoken " + self.accesstoken}

        respObj = requests.post(url, data=importConfig, files=files, headers=headers)

        # To generate new access token once after it expires.
        if self.invalidOAUTH(respObj):
            self.accesstoken = self.getOAuthToken()
            headers = {"Authorization": "Zoho-oauthtoken " + self.accesstoken}
            respObj = requests.post(url, data=importConfig, files=files, headers=headers)

        if (respObj.status_code != 200):
            raise ServerError(respObj)
        else:
            return ImportResult(respObj.content)

    def importData_v1a(self, tableURI: str, import_mode: str,
                       import_content: str,
                       matching_columns: str = None,
                       date_format=None,
                       import_config=None,
                       retry_countdown=0) -> 'ImportResult':
        """ Send data to zoho using a string formatted in CSV style.
        This has been refactored to use requests.post.
        Bulk import data into the table identified by the URI. import_content is a string in csv format (\n separated)
        The first line is column headers.
        Note: the API supports JSON too but it is not implemented here.
        raises RuntimeError if api limits are exceeded

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
        @param matching_columns: A comma separated list of column names to match on.  If this is not provided, then the first column is used.
        @type matching_columns:string
        @param date_format: The Zoho date format to use.  If this is not provided, then the default is used.
        @type date_format:string
        @param retry_countdown: The number of retries to attempt if the API returns a recoverable error.  If this is not provided, then the default is used.
        @type retry_countdown:int
        @return: An L{ImportResult} containing the results of the Import
        @rtype:L{ImportResult}
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        date_format = date_format or "yyyy-MM-dd"

        payload = {"ZOHO_AUTO_IDENTIFY": "true",
                   # "ZOHO_COMMENTCHAR":"#",
                   # "ZOHO_DELIMITER":0, #comma
                   # "ZOHO_QUOTED":2, #double quote
                   "ZOHO_ON_IMPORT_ERROR": "ABORT",
                   "ZOHO_CREATE_TABLE": "false", "ZOHO_IMPORT_TYPE": import_mode,
                   "ZOHO_DATE_FORMAT": date_format,
                   "ZOHO_IMPORT_DATA": import_content}

        if matching_columns:
            payload['ZOHO_MATCHING_COLUMNS'] = matching_columns

        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "IMPORT", "XML")
        r = self.__sendRequest(url=url, httpMethod="POST", payLoad=payload, action="IMPORT", callBackData=None,
                               retry_countdown=retry_countdown)
        return ImportResult(r.response)  # a parser from Zoho

    def importDataAsString(self, tableURI, importType, importContent, autoIdentify, onError, importConfig=None):
        """
        Bulk import data into the table identified by the URI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param importType: The type of import.
        Can be one of
         1. APPEND
         2. TRUNCATEADD
         3. UPDATEADD
        See U{Import types<https://www.zoho.com/analytics/api/#import-data>} for more details.
        @type importType:string
        @param importContent: The data in csv format or json.
        @type importContent:string
        @param autoIdentify: Used to specify whether to auto identify the CSV format. Allowable values - true/false.
        @type autoIdentify:string
        @param onError: This parameter controls the action to be taken In-case there is an error during import.
        @type onError:string
        @param importConfig: Contains any additional control parameters.
        See U{Import types<https://www.zoho.com/analytics/api/#import-data>} for more details.
        @type importConfig:dictionary
        @return: An L{ImportResult} containing the results of the Import.
        @rtype:L{ImportResult}
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        dict = {"ZOHO_AUTO_IDENTIFY": autoIdentify, "ZOHO_ON_IMPORT_ERROR": onError,
                "ZOHO_IMPORT_TYPE": importType, "ZOHO_IMPORT_DATA": importContent}

        if not ("ZOHO_CREATE_TABLE" in importConfig):
            importConfig["ZOHO_CREATE_TABLE"] = 'false'

        payLoad = ReportClientHelper.getAsPayLoad([dict, importConfig], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "IMPORT", "XML")
        return self.__sendRequest(url, "POST", payLoad, "IMPORT", None)

    def exportData(self, tableOrReportURI, format, exportToFileObj,
                   criteria: Optional[str] = None, config: Optional[str] = None):
        """
        Export the data in the  specified table identified by the URI.
        @param tableOrReportURI: The URI of the table. See L{getURI<getURI>}.
        @type tableOrReportURI:string
        @param format: The format in which the data is to be exported.
        See U{Supported Export Formats<https://www.zoho.com/analytics/api/#export-data>} for
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
        url = ReportClientHelper.addQueryParams(tableOrReportURI, self.access_token, "EXPORT", format)
        return self.__sendRequest(url, "POST", payLoad, "EXPORT", exportToFileObj)

    def exportDataUsingSQL(self, tableOrReportURI, format, exportToFileObj, sql, config=None):
        """
        Export the data with the  specified SQL query identified by the URI.
        @param tableOrReportURI: The URI of the workspace. See L{getDBURI<getDBURI>}.
        @type tableOrReportURI:string
        @param format: The format in which the data is to be exported.
        See U{Supported Export Formats<https://www.zoho.com/analytics/api/#export-data>} for
        the supported types.
        @type format:string
        @param exportToFileObj: File (or file like object) to which the exported data is to be written
        @type exportToFileObj:file
        @param sql: The sql whose output need to be exported.
        @type sql:string
        @param config: Contains any additional control parameters. Can be C{None}.

        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.

        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, sql)
        url = ReportClientHelper.addQueryParams(tableOrReportURI, self.access_token, "EXPORT", format)
        return self.__sendRequest(url, "POST", payLoad, "EXPORT", exportToFileObj)

    def exportDataUsingSQL_v2(self, tableOrReportURI, format, sql, config=None, retry_countdown=0) -> io.BytesIO:
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
        @param retry_countdown: Number of retry attempts allowed.  If 0, no retries are attempted.
        @type retry_countdown:int
        @raise ServerError: If the server has recieved the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """

        # this is a bug in Zoho's Python library. The SQL query must be passed as a parameter, not in the body.
        # in the body, it is ignored.
        # payload = ReportClientHelper.getAsPayLoad([config], None, sql)
        payload = None
        """ sql does not need to URL encoded when passed in, but wrap in quotes"""
        # addQueryParams  adds parameters to the URL, not in the POST body but that seems ok for zoho..   url += "&ZOHO_ERROR_FORMAT=XML&ZOHO_ACTION=" + urllib.parse.quote(action)
        # addQueryParams adds: ZOHO_ERROR_FORMAT, ZOHO_OUTPUT_FORMAT
        url = ReportClientHelper.addQueryParams(tableOrReportURI, self.access_token, "EXPORT", format,
                                                sql=sql)  # urlencoding is done in here
        callback_object = io.BytesIO()
        r = self.__sendRequest(url=url, httpMethod="POST", payLoad=payload, action="EXPORT",
                               callBackData=callback_object, retry_countdown=retry_countdown)
        return callback_object

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "COPYDATABASE", "JSON")
        return self.__sendRequest(url, "POST", payLoad, "COPYDB", None)

    def copy_workspace_api_v2(self, workspace_id, new_workspace_name, workspace_key, copy_with_data: bool,
                              source_org_id,
                              dest_org_id,
                              copy_with_import_source: bool = False,

                              ):
        """
       A v2 API functions
        """
        config_dict = {"newWorkspaceName": new_workspace_name, "newWorkspaceDesc": f"copy",
                       "workspaceKey": workspace_key,
                       "copyWithData": copy_with_data,
                       "copyWithImportSource": copy_with_import_source}

        config_data = "CONFIG=" + urllib.parse.quote_plus(json.dumps(config_dict))
        url = self.getURI_v2() + f"workspaces/{workspace_id}"

        extra_headers = {"ZANALYTICS-ORGID": source_org_id, "ZANALYTICS-DEST-ORGID": dest_org_id}
        return self.__sendRequest(url, "POST", payLoad=None, params=config_data, action=None,
                                  extra_headers=extra_headers)

    def get_orgs_metadata_api_v2(self):
        url = self.getURI_v2() + f"orgs/"
        return self.__sendRequest(url, "GET", payLoad=None, action=None)

    def get_all_workspaces_metadata_api_v2(self) -> ZohoWorkspacesResponse:
        url = self.getURI_v2() + f"workspaces/"
        return self.__sendRequest(url, "GET", payLoad=None, action=None)

    def get_views_api_v2(self, org_id: str, workspace_id: str, view_types: list[int] = None) -> ZohoWorkspacesResponse:
        """ViewType:
        0 - Table
        1 - Tabular View
        2 - AnalysisView / Chart
        3 - Pivot
        4 - SummaryView
        6 - QueryTable
        7 - Dashboard"""
        url = self.getURI_v2() + f"workspaces/{workspace_id}/views/"
        if view_types:
            url += f"?viewTypes={','.join(map(str, view_types))}"
        return self.__sendRequest(url, "GET", payLoad=None, action=None, extra_headers={"ZANALYTICS-ORGID": org_id})

    def get_view_details_api_v2(self,view_id):
        url = self.getURI_v2() + f"views/{view_id}"
        config_dict = {"withInvolvedMetaInfo":True}
        json_config = json.dumps(config_dict)
        # URL-encode the JSON string
        # quote_plus is generally preferred for query parameters as it encodes spaces as '+'
        encoded_config = urllib.parse.quote_plus(json_config)
        url += f"?CONFIG={encoded_config}"

        return self.__sendRequest(url, "GET", payLoad=None, action=None)


    def get_meta_details_view_api_v2(self,org_id:str,workspace_name:str,view_name:str):
        url = self.getURI_v2() + f"metadetails"
        config_dict = {"workspaceName": workspace_name, "viewName": view_name}
        # Convert the dictionary to a JSON string
        json_config = json.dumps(config_dict)
        # URL-encode the JSON string
        # quote_plus is generally preferred for query parameters as it encodes spaces as '+'
        encoded_config = urllib.parse.quote_plus(json_config)
        url += f"?CONFIG={encoded_config}"
        extra_headers = {"ZANALYTICS-ORGID": org_id, }
        return self.__sendRequest(url, "GET", payLoad=None, action=None,extra_headers=extra_headers)


    def get_workspace_secretkey_api_v2(self, workspace_id:str, org_id:str):
        extra_headers = {"ZANALYTICS-ORGID": org_id, }
        url = self.getURI_v2() + f"workspaces/{workspace_id}/secretkey"
        return self.__sendRequest(url, "GET", payLoad=None, action=None, extra_headers=extra_headers)

    def get_workspace_details_api_v2(self, workspace_id):
        extra_headers = None
        url = self.getURI_v2() + f"workspaces/{workspace_id}"
        return self.__sendRequest(url, "GET", payLoad=None, action=None, extra_headers=extra_headers)

    def delete_workspace_api_v2(self, workspace_id: str, org_id: str):
        extra_headers = {"ZANALYTICS-ORGID": org_id}
        url = self.getURI_v2() + f"workspaces/{workspace_id}"
        return self.__sendRequest(url, "DELETE", payLoad=None, action=None, extra_headers=extra_headers)

    def deleteDatabase(self, userURI, databaseName, config=None):
        """
        delete_workspace_api_v2 makes this redundant
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "DELETEDATABASE", "XML")
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
        url = ReportClientHelper.addQueryParams(userUri, self.access_token, "ENABLEDOMAINDB", "JSON")
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
        url = ReportClientHelper.addQueryParams(userUri, self.access_token, "DISABLEDOMAINDB", "JSON")
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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "CREATETABLE", "JSON")
        # url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote(tableDesign)
        url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote_plus(tableDesign)  # smaller URL, fits under limit better

        return self.__sendRequest(url, "POST", payLoad, "CREATETABLE", None)

    def createTable_v2(self, workspace_id, org_id,tableDesign:AnalyticsTableZohoDef_v2, config=None):
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
        url = self.getURI_v2() + f"workspaces/{workspace_id}/tables"

        json_config=json.dumps({"tableDesign":tableDesign})
        encoded_config = urllib.parse.quote_plus(json_config)
        url += f"?CONFIG={encoded_config}"
        extra_headers = {"ZANALYTICS-ORGID": org_id, }
        return self.__sendRequest(url, "POST", payLoad=None, action=None,extra_headers=extra_headers)




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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "AUTOGENREPORTS", "JSON")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "CREATESIMILARVIEWS", "JSON")
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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "RENAMEVIEW", "XML")
        url += "&ZOHO_VIEWNAME=" + urllib.parse.quote(viewName)
        url += "&ZOHO_NEW_VIEWNAME=" + urllib.parse.quote(newViewName)
        url += "&ZOHO_NEW_VIEWDESC=" + urllib.parse.quote(viewDesc)
        self.__sendRequest(url, "POST", payLoad, "RENAMEVIEW", None)

    def saveAs(self, dbURI, viewToCopy, newViewName, config=None):
        """
        Create a new view by copying the structure and data of existing view.
        @param dbURI: The URI of the workspace. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param viewToCopy: Name of the view to be copied.
        @type viewToCopy:string
        @param newViewName: Name of the view to be created.
        @type newViewName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: The status about the request (success or failure).
        @rtype: string
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "SAVEAS", "JSON")
        url += "&ZOHO_VIEWTOCOPY=" + urllib.parse.quote(viewToCopy)
        url += "&ZOHO_NEW_VIEWNAME=" + urllib.parse.quote(newViewName)
        return self.__sendRequest(url, "POST", payLoad, "SAVEAS", None)

    def copyReports(self, dbURI, views, dbName, dbKey, config=None):
        """
        The Copy Reports API is used to copy one or more reports from one database to another within the same account or even across user accounts.
        @param dbURI: The URI of the source database. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param views: This parameter holds the list of view names.
        @type views:string
        @param dbName: The database name where the reports are to be copied.
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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "COPYREPORTS", "XML")
        url += "&ZOHO_VIEWTOCOPY=" + urllib.parse.quote(views)
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        url += "&ZOHO_COPY_DB_KEY=" + urllib.parse.quote(dbKey)
        return self.__sendRequest(url, "POST", payLoad, "COPYREPORTS", None)

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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "COPYFORMULA", "XML")
        url += "&ZOHO_FORMULATOCOPY=" + urllib.parse.quote(formula)
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        url += "&ZOHO_COPY_DB_KEY=" + urllib.parse.quote(dbKey)
        return self.__sendRequest(url, "POST", payLoad, "COPYREPORTS", None)

    def addColumn(self, tableURI, columnName, dataType: DataTypeAddColumn, config=None):
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "ADDCOLUMN", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        url += "&ZOHO_DATATYPE=" + urllib.parse.quote(dataType)
        return self.__sendRequest(url, "POST", payLoad, "ADDCOLUMN", None)

    def addColumn_v2(self, org_id:str, workspace_id:str, view_id:str, column_def:ColumnDef_v2):
        """
        adds a column,would be nice to lookups too but it's alot of work need the view id and reference id of the other column
        """
        url = self.getURI_v2() + f"workspaces/{workspace_id}/views/{view_id}/columns"
        json_config=json.dumps({"columnName":column_def["COLUMNNAME"], "dataType":column_def["DATATYPE"]})
        encoded_config = urllib.parse.quote_plus(json_config)
        url += f"?CONFIG={encoded_config}"
        extra_headers = {"ZANALYTICS-ORGID": org_id, }
        add_col_result =  self.__sendRequest(url, "POST", payLoad=None, action=None,extra_headers=extra_headers)

        # if "LOOKUPCOLUMN" in col_def:
        #     url = self.getURI_v2() + f"workspaces/{workspace_id}/views/{view_id}/columns"
        #     json_config = json.dumps({"columnName": col_def["COLUMNNAME"], "dataType": col_def["DATATYPE"]})
        #     encoded_config = urllib.parse.quote_plus(json_config)
        #     url += f"?CONFIG={encoded_config}"
        #     extra_headers = {"ZANALYTICS-ORGID": org_id, }
        #     add_col_result = self.__sendRequest(url, "POST", payLoad=None, action=None, extra_headers=extra_headers)



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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "DELETECOLUMN", "XML")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "RENAMECOLUMN", "XML")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "HIDECOLUMN", "JSON")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "SHOWCOLUMN", "JSON")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "ADDLOOKUP", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        url += "&ZOHO_REFERREDTABLE=" + urllib.parse.quote(referedTable)
        url += "&ZOHO_REFERREDCOLUMN=" + urllib.parse.quote(referedColumn)
        url += "&ZOHO_IFERRORONCONVERSION=" + urllib.parse.quote(onError)
        return self.__sendRequest(url, "POST", payLoad, "ADDLOOKUP", None)

    def removeLookup(self, tableURI, columnName, config=None):
        """
        Remove the lookup for the given column.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: Name of the column.
        @type columnName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "REMOVELOOKUP", "XML")
        url += "&ZOHO_COLUMNNAME=" + urllib.parse.quote(columnName)
        return self.__sendRequest(url, "POST", payLoad, "REMOVELOOKUP", None)

    def createBlankDb(self, userURI, dbName, dbDesc, config=None):
        """
        Create a blank workspace.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param dbName: The workspace name.
        @type dbName:string
        @param dbDesc: The workspace description.
        @type dbDesc:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "CREATEBLANKDB", "JSON")
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        if (dbDesc != None):
            url += "&ZOHO_DATABASE_DESC=" + urllib.parse.quote(dbDesc)
        self.__sendRequest(url, "POST", payLoad, "CREATEBLANKDB", None)

    def getDatabaseMetadata(self, requestURI, metadata, config=None):
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
        payload = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(requestURI, self.access_token, "DATABASEMETADATA", "JSON")
        url += "&ZOHO_METADATA=" + urllib.parse.quote(metadata)
        r = self.__sendRequest(url=url, httpMethod="POST", payLoad=payload, action="DATABASEMETADATA",
                               callBackData=None)
        return r

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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETDATABASENAME", "XML")
        url += "&DBID=" + urllib.parse.quote(dbid)
        return self.__sendRequest(url, "POST", payLoad, "GETDATABASENAME", None)

    def getDatabaseID(self, userURI, dbName, config=None):
        """
        Get workspace ID for a specified workspace identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param dbName: The name of the workspace.
        @type dbName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: The workspace ID.
        @rtype: string
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETDATABASEID", "XML")
        url += "&ZOHO_DATABASE_NAME=" + urllib.parse.quote(dbName)
        return self.__sendRequest(url, "POST", payLoad, "GETDATABASEID", None)

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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "ISDBEXIST", "JSON")
        url += "&ZOHO_DB_NAME=" + urllib.parse.quote(dbName)
        return self.__sendRequest(url, "POST", payLoad, "ISDBEXIST", None)

    def isViewExist(self, dbURI, viewName, config=None):
        """
        Checks whether the view exist or not in the workspace identified by dbURI.
        @param dbURI: The URI of the workspace. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param viewName: Name of the view.
        @type viewName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Returns True, if view exist. False, otherwise.
        @rtype:string
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "ISVIEWEXIST", "JSON")
        url += "&ZOHO_VIEW_NAME=" + urllib.parse.quote(viewName)
        return self.__sendRequest(url, "POST", payLoad, "ISVIEWEXIST", None)

    def isColumnExist(self, tableURI, columnName, config=None):
        """
        Checks whether the column exist or not in the workspace identified by tableURI.
        @param tableURI: The URI of the table. See L{getURI<getURI>}.
        @type tableURI:string
        @param columnName: Name of the column.
        @type columnName:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @return: Returns True, if column exist. False, otherwise.
        @rtype:string
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "ISCOLUMNEXIST", "JSON")
        url += "&ZOHO_COLUMN_NAME=" + urllib.parse.quote(columnName)
        return self.__sendRequest(url, "POST", payLoad, "ISCOLUMNEXIST", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "GETCOPYDBKEY", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETVIEWNAME", "XML")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "GETINFO", "XML")
        return self.__sendRequest(url, "POST", payLoad, "GETINFO", None)

    def getViewInfo(self, dbURI, viewID, config=None):
        """
        Returns view details like view name,description,type from the the particular workspace identified by dbURI.
        @param dbURI: The URI of the workspace. See L{getDBURI<getDBURI>}.
        @type dbURI:string
        @param viewID: The ID of the view.
        @type viewID:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: The information about the view.
        @rtype: dictionary
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "GETVIEWINFO", "JSON")
        url += "&ZOHO_VIEW_ID=" + urllib.parse.quote(viewID)
        return self.__sendRequest(url, "GET", payLoad, "GETVIEWINFO", None)

    def recentItems(self, userURI, config=None):
        """
        Returns the details of recently accessed views from the ZohoAnalytics account identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Recently modified views.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "RECENTITEMS", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "RECENTITEMS", None)

    def getDashboards(self, userURI, config=None):
        """
        Returns the list of owned/shared dashboards present in the zoho analytics account identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: The details of dashboards present in the organization.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETDASHBOARDS", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "GETDASHBOARDS", None)

    def myWorkspaceList(self, userURI, config=None):
        """
        Returns the list of all owned workspaces present in the ZohoAnalytics account identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Metainfo of owned workspaces present in the organization.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "MYWORKSPACELIST", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "MYWORKSPACELIST", None)

    def sharedWorkspaceList(self, userURI, config=None):
        """
        Returns the list of all shared workspaces present in the ZohoAnalytics account identified by the URI.
        @param userURI: The URI of the user. See L{getUserURI<getUserURI>}.
        @type userURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Metainfo of shared workspaces present in the organization.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "SHAREDWORKSPACELIST", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "SHAREDWORKSPACELIST", None)

    def viewList(self, dbURI, config=None):
        """
        Returns the list of all accessible views present in the workspace identified by the URI.
        @param dbURI: The URI of the workspace. See L{getUserURI<getUserURI>}.
        @type dbURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Metainfo of all accessible views present in the workspace.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "VIEWLIST", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "VIEWLIST", None)

    def folderList(self, dbURI, config=None):
        """
        Returns the list of all accessible views present in the workspace identified by the URI.
        @param dbURI: The URI of the workspace. See L{getUserURI<getUserURI>}.
        @type dbURI:string
        @param config: Contains any additional control parameters. Can be C{None}.
        @type config:dictionary
        @raise ServerError: If the server has received the request but did not process the request
        due to some error.
        @raise ParseError: If the server has responded but client was not able to parse the response.
        @return: Metainfo of all accessible folders present in the workspace.
        @rtype:List
        """
        payLoad = ReportClientHelper.getAsPayLoad([config], None, None)
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "FOLDERLIST", "JSON")
        return self.__sendRequest(url, "GET", payLoad, "FOLDERLIST", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "SHARE", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        url += "&ZOHO_VIEWS=" + urllib.parse.quote(views)
        return self.__sendRequest(url, "POST", payLoad, "SHARE", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "REMOVESHARE", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "REMOVESHARE", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "ADDDBOWNER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "ADDDBOWNER", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "REMOVEDBOWNER", "XML")
        url += "&ZOHO_EMAILS=" + urllib.parse.quote(emailIds)
        return self.__sendRequest(url, "POST", payLoad, "REMOVEDBOWNER", None)

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
        url = ReportClientHelper.addQueryParams(dbURI, self.access_token, "GETSHAREINFO", "JSON")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "GETVIEWURL", "XML")
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
        url = ReportClientHelper.addQueryParams(tableURI, self.access_token, "GETEMBEDURL", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETUSERS", "JSON")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "ADDUSER", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "REMOVEUSER", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "ACTIVATEUSER", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "DEACTIVATEUSER", "XML")
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
        url = ReportClientHelper.addQueryParams(userURI, self.access_token, "GETUSERPLANDETAILS", "XML")
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

    def getURI(self, dbOwnerName: str, dbName: str, tableOrReportName: str) -> str:
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

    def getURI_v2(self) -> str:
        """
        Returns the base URL for v2 api with trailing /
        """
        url = self.reportServerURL + "/restapi/v2/"

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


class RecoverableRateLimitError(Exception):
    """
    RatelimitError is thrown if the report server has received a ratelimit error.
    """

    def __init__(self, urlResp, **kwargs):
        self.httpStatusCode = urlResp.status_code  # :The http status code for the request.
        self.errorCode = self.httpStatusCode  # The error code sent by the server.
        self.uri = ""  # : The uri which threw this exception.
        self.action = ""  # :The action to be performed over the resource specified by the uri
        if hasattr(urlResp, 'response') and urlResp.response is not None:
            self.message = urlResp.response.text
        else:
            self.message = urlResp.content  # : Returns the message sent by the server.
        self.zoho_error_code = kwargs.get("zoho_error_code")
        self.extra = kwargs
        super().__init__(self.message)


class UnrecoverableRateLimitError(Exception):
    """
    RatelimitError is thrown if the report server has received a ratelimit error.
    """

    def __init__(self, urlResp, **kwargs):
        self.httpStatusCode = urlResp.status_code  # :The http status code for the request.
        self.errorCode = self.httpStatusCode  # The error code sent by the server.
        self.uri = ""  # : The uri which threw this exception.
        self.action = ""  # :The action to be performed over the resource specified by the uri
        if hasattr(urlResp, 'response') and urlResp.response is not None:
            self.message = urlResp.response.text
        else:
            self.message = urlResp.content  # : Returns the message sent by the server.
        self.zoho_error_code = kwargs.get("zoho_error_code")
        self.extra = kwargs
        super().__init__(self.message)


class ServerError(Exception):
    """
    ServerError is thrown if the report server has received the request but did not process the
    request due to some error. For example if authorization failure.
    """

    def __init__(self, urlResp, **kwargs):
        self.httpStatusCode = urlResp.status_code  #:The http status code for the request.
        self.errorCode = self.httpStatusCode  # The error code sent by the server.
        self.uri = ""  #: The uri which threw this exception.
        self.action = ""  #:The action to be performed over the resource specified by the uri
        self.message = urlResp.content  #: Returns the message sent by the server.
        self.zoho_error_code = kwargs.get("zoho_error_code")
        self.extra = kwargs

        parseable = False
        if not urlResp:
            logger.error(f"response object is None")
        else:
            try:
                contHeader = urlResp.headers.get("Content-Type", None)
                if (contHeader and contHeader.find("text/xml") > -1):
                    self.__parseErrorResponse()
            except AttributeError:
                logger.error(f"response object is None")
        super().__init__(self.message)


class BadDataError(Exception):
    def __init__(self, urlResp, **kwargs):
        self.httpStatusCode = urlResp.status_code  #:The http status code for the request.
        self.errorCode = self.httpStatusCode  # The error code sent by the server.
        self.uri = ""  #: The uri which threw this exception.
        self.action = ""  #:The action to be performed over the resource specified by the uri
        self.message = urlResp.content  #: Returns the message sent by the server.
        self.zoho_error_code = kwargs.get("zoho_error_code")
        self.extra = kwargs

        parseable = False
        if not urlResp:
            logger.error(f"response object is None")
        else:
            try:
                contHeader = urlResp.headers.get("Content-Type", None)
                if (contHeader and contHeader.find("text/xml") > -1):
                    self.__parseErrorResponse()
            except AttributeError:
                logger.error(f"response object is None")
        super().__init__(self.message)


class ParseError(Exception):
    """
    ParseError is thrown if the server has responded but client was not able to parse the response.
    Possible reasons could be version mismatch.The client might have to be updated to a newer version.
    """

    def __init__(self, responseContent, message, origExcep):
        super().__init__(message)
        self.responseContent = responseContent  #: The complete response content as sent by the server.
        self.message = message  #: The message describing the error.
        self.origExcep = repr(origExcep)  #: The original exception that occurred during parsing(Can be C{None}).


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

        except ParseError as e:
            # logger.debug(f"Note in import result: could not find result code {msg}")
            self.result_code = 0

        try:
            self.totalColCount = int(ReportClientHelper.getInfo(dom, "totalColumnCount", response))
        except ParseError as e:
            logger.debug(f"Error in import result: did not get a good return message: {msg}")
            raise ParseError(responseContent=msg, message=None, origExcep=None)
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

    def __init__(self, resp: requests.Response):
        """ updated to assume a urllib3 object"""
        self.content = getattr(resp, 'content', None)
        self.reason = getattr(resp, 'reason', None)  # This is used for communication about errors
        self.status_code = getattr(resp, 'status_code', None)
        self.headers = {}
        self.headers = getattr(resp, 'headers', None)
        self.response = resp


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
    def addQueryParams(url, authtoken, action, exportFormat, sql=None, criteria=None, table_design=None):
        url = ReportClientHelper.checkAndAppendQMark(url)
        url += "&ZOHO_ERROR_FORMAT=JSON&ZOHO_ACTION=" + urllib.parse.quote(action)
        url += "&ZOHO_OUTPUT_FORMAT=" + urllib.parse.quote(exportFormat)
        url += "&ZOHO_API_VERSION=" + ReportClientHelper.API_VERSION
        if ReportClient.isOAuth == False:
            url += "&authtoken=" + urllib.parse.quote(authtoken)
        if exportFormat == "JSON":
            url += "&ZOHO_VALID_JSON=TRUE"
        if sql:
            url += "&ZOHO_SQLQUERY=" + urllib.parse.quote(sql)
        if criteria:
            url += "&ZOHO_CRITERIA=" + urllib.parse.quote(criteria)
        if table_design:
            # quote_plus seems to work and it makes for a smaller URL avoiding problems with a URL too long
            url += "&ZOHO_TABLE_DESIGN=" + urllib.parse.quote_plus(table_design)
        return url

    @staticmethod
    def getAsPayLoad(separateDicts, criteria: Optional[str], sql: Optional[str], encode_payload=False):
        payload = {}
        for i in separateDicts:
            if (i != None):
                payload.update(i)

        if (criteria != None):
            payload["ZOHO_CRITERIA"] = criteria

        if (sql != None):
            payload["ZOHO_SQLQUERY"] = sql

        if len(payload) != 0:
            if encode_payload:
                payload = urllib.parse.urlencode(payload)
            else:
                pass
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
