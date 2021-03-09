""" Wrapper class over Zoho's ReportClient. This is more modern and higher level.

"""

import csv
import logging
from typing import MutableMapping, Optional
import time
import json

import requests
from . import report_client as report_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

""" add some helper functions on top of report_client"""


class EnhancedZohoAnalyticsClient(report_client.ReportClient):

    @staticmethod
    def process_table_meta_data(catalog,force_lowercase_column_names=False):
        """ catalog is a ZOHO_CATALOG_INFO dict. Call this from get_database_metadata for example
         Return a dict keyed by tablename, each item being a dict keyed by column name, with the item being the
         catalog info for the col
         So all the table names can be found as table_data.keys()
         for for a given table name, the column names are table_data['table1'].keys()
         and to find the column meta data such as dataType:
         data['table1']['col1']['typeName']
         Zoho gives each type an integer coding ['dataType'], a descriptive datatype name ['typeName'],
         and some other meta data.

         """
        db_name = catalog['tableCat']
        table_data = {}
        for table in catalog['views']:
            if table['tableType'] == 'TABLE':
                table_data[table['tableName']] = {}
                col_data = table_data[table['tableName']]
                for col in table['columns']:
                    if force_lowercase_column_names:
                        col_data[col['columnName'].lower()] = col
                    else:
                        col_data[col['columnName']] = col

        return table_data

    def __init__(self, login_email_id: str, token: str, default_databasename: str = None, clientId=None,
                 clientSecret=None,serverURL=None,reportServerURL=None):
        self.login_email_id = login_email_id
        self.default_databasename = default_databasename
        super().__init__(token=token, clientId=clientId, clientSecret=clientSecret,serverURL=serverURL,reportServerURL=reportServerURL)

    def get_database_catalog(self, database_name: str = None) -> MutableMapping:
        db_uri = self.getDBURI(self.login_email_id, database_name or self.default_databasename)
        catalog_info = self.getDatabaseMetadata(requestURI=db_uri, metadata="ZOHO_CATALOG_INFO")
        return catalog_info

    def get_table_metadata(self, database_name: str = None,force_lowercase_column_names=False) -> MutableMapping:
        database_name = database_name or self.default_databasename
        catalog_info = self.get_database_catalog(database_name=database_name)
        table_metadata = self.process_table_meta_data(catalog_info,force_lowercase_column_names=force_lowercase_column_names)
        return table_metadata

    def create_table(self, table_design, database_name=None) -> MutableMapping:
        db_uri = self.getDBURI(self.login_email_id, database_name or self.default_databasename)
        columns = table_design['COLUMNS']
        if len(columns) < 70:  # too many columns and zoho rejects the very long URL
            result = self.createTable(dbURI=db_uri, tableDesign=json.dumps(table_design))
        else:
            columns_initial, columns_residual = columns[:70], columns[70:]
            table_design['COLUMNS'] = columns_initial
            table_name = table_design['TABLENAME']
            result = self.createTable(dbURI=db_uri, tableDesign=json.dumps(table_design))
            uri_addcol = self.getURI(self.login_email_id, database_name or self.default_databasename,
                                     tableOrReportName=table_name)
            for col in columns_residual:
                self.addColumn(tableURI=uri_addcol, columnName=col['COLUMNNAME'], dataType=col['DATATYPE'])

        return result

    def data_upload(self, import_content: str, table_name: str, import_mode="TRUNCATEADD",
                    matching_columns: Optional[str] = None,
                    database_name: Optional[str] = None,
                    retry_limit=9,
                    date_format=None) -> Optional[report_client.ImportResult]:
        """ data is a csv-style string, newline separated. Matching columns is a comma separated string"""
        retry_count = 0
        impResult = None
        database_name = database_name or self.default_databasename
        uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name, tableOrReportName=table_name)
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
        impResult = self.importData_v2(uri, import_mode=import_mode, import_content=import_content,
                                       date_format=date_format,
                                       matching_columns=matching_columns, retry_countdown=retry_limit)
        logger.debug(
                f"Table: {table_name}: Processed Rows: "
                f"{impResult.totalRowCount} with {impResult.warningCount} warnings ")
        # while True:
        #     retry_count += 1
        #     try:
        #         impResult = self.importData_v2(uri, import_mode=import_mode, import_content=import_content,
        #                                        date_format=date_format,
        #                                        matching_columns=matching_columns,retry_countdown=retry_limit)
        #         logger.debug(
        #             f"Table: {table_name}: Processed Rows: "
        #             f"{impResult.totalRowCount} with {impResult.warningCount} warnings ")
        #         break
        #     except report_client.RecoverableRateLimitError:
        #         if retry_count <= retry_limit:
        #             logger.error(f"Zoho API limit or some other recoverable error, will retry, next attempt: {retry_count}")
        #             time.sleep(retry_count * 10)
        #             continue
        #             # raise RuntimeError("API limit exceeded")
        #         else:
        #             logger.info(f"Number of retry attempts exceeded")
        #             raise RuntimeError("API Limit error: Number of retry attempts exceeded")
        #     except report_client.UnrecoverableRateLimitError:
        #         logger.error(f"Zoho API daily limit exceeded or row count exceeded, will not retry")
        #         raise
        #     except report_client.ParseError as e:
        #         response_content_string = e.responseContent.decode('utf-8', errors='ignore')
        #         response_content_string = response_content_string or 'No response content'
        #         if 'Invalid NUMBER value' in response_content_string:
        #             raise RuntimeError(
        #                 f"Invalid data format in Zoho data upload, check table definitions: {response_content_string}")
        #         if retry_count <= retry_limit:
        #             logger.error(f"Retrying data_upload because of upload error: {response_content_string}")
        #             time.sleep(1)
        #             continue
        #         else:
        #             logger.info(f"Number of retry attempts exceeded")
        #             raise (requests.exceptions.ConnectionError(response_content_string))
        return impResult


    def data_export_using_sql(self, sql, table_name, database_name: str = None, cache_object = None, cache_timeout_seconds=60, retry_countdown = 0) -> csv.DictReader:
        """ returns a csv.DictReader after querying with the sql provided.
        The Zoho API insists on a table or report name, but it doesn't seem to restrict the query
        The cache object has a get and set function like the django cache does: https://docs.djangoproject.com/en/3.1/topics/cache/
        The cache key is the sql query"""

        if cache_object:
            returned_data = cache_object.get(sql)
        else:
            returned_data = None
        if not returned_data:
            database_name = database_name or self.default_databasename
            uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name or self.default_databasename,
                              tableOrReportName=table_name)
            callback_data = self.exportDataUsingSQL_v2(tableOrReportURI=uri, format='CSV', sql=sql,retry_countdown=retry_countdown)
            returned_data = callback_data.getvalue().decode('utf-8').splitlines()
            if cache_object:
                cache_object.set(sql,returned_data,cache_timeout_seconds)

        reader = csv.DictReader(returned_data)
        return reader

    def delete_rows(self, table_name, sql, database_name: Optional[str] = None,retry_countdown=0):
        """ criteria is SQL fragments such as 'a' in ColA """
        uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name or self.default_databasename,
                          tableOrReportName=table_name)

        r = self.deleteData(tableURI=uri, criteria=sql,retry_countdown=retry_countdown)
        return r
