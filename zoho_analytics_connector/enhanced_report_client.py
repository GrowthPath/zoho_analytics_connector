""" Wrapper class over Zoho's ReportClient. This is more modern and higher level.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""

import csv
import json
import logging
import time
from typing import MutableMapping, Optional, List, Callable

from . import report_client
from .model_helpers import AnalyticsTableZohoDef_v2

from .typed_dicts import ZohoSchemaModel, TableView, Catalog, ZohoSchemaModel_v2, TableView_v2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

""" add some helper functions on top of report_client"""


class EnhancedZohoAnalyticsClient(report_client.ReportClient):
    @staticmethod
    def process_table_meta_data(catalog:Catalog, force_lowercase_column_names=False)->ZohoSchemaModel:
        """ catalog is a ZOHO_CATALOG_INFO dict. Call this from get_database_metadata for example
         Return a dict keyed by tablename, each item being a dict keyed by column name, with the item being the
         catalog info for the col
         So all the table names can be found as table_data.keys()
         for a given table name, the column names are table_data['table1'].keys()
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

    @staticmethod
    def process_table_meta_data_v2(catalog:dict[str,TableView_v2], force_lowercase_column_names=False)->ZohoSchemaModel_v2:
        """ catalog is a ZOHO_CATALOG_INFO dict. Call this from get_database_metadata for example
         Return a dict keyed by tablename, each item being a dict keyed by column name, with the item being the
         catalog info for the col
         So all the table names can be found as table_data.keys()
         for a given table name, the column names are table_data['table1'].keys()
         and to find the column meta data such as dataType:
         data['table1']['col1']['typeName']
         Zoho gives each type an integer coding ['dataType'], a descriptive datatype name ['typeName'],
         and some other meta data.

         """
        table_data_zoho_schema:ZohoSchemaModel_v2 = {}
        for table_name,table in catalog.items():
            if table['tableType'] == 'Table':
                zoho_schema_model = {d["columnName"]:d for d in table['columns']}
                table_data_zoho_schema[table_name] = zoho_schema_model

        return table_data_zoho_schema


    def __init__(self, login_email_id: str, refresh_token: str, default_databasename: str = None, access_token: str = None, clientId=None,
                 clientSecret=None, serverURL=None, reportServerURL=None, default_retries=None,
                 reporting_currency: str = None,
                 error_email_list: Optional[List[str]] = None,
                 token_persistence_callback: Optional[Callable[[str], None]] = None):
        """ error email list is not used by the client, but it is available for callers as a convenience"""
        self.login_email_id = login_email_id
        self.default_databasename = default_databasename
        self.error_email_list = error_email_list or [login_email_id]
        self.reporting_currency = reporting_currency
        self.token_persistence_callback = token_persistence_callback
        super().__init__(refresh_token=refresh_token, clientId=clientId, clientSecret=clientSecret, serverURL=serverURL,
                         reportServerURL=reportServerURL, default_retries=default_retries, access_token=access_token)

    def persist_token(self, token: str):
        if self.token_persistence_callback:
            self.token_persistence_callback(token)

    def get_database_catalog(self, database_name: str = None) -> Catalog:
        db_uri = self.getDBURI(self.login_email_id, database_name or self.default_databasename)
        catalog_info = self.getDatabaseMetadata(requestURI=db_uri, metadata="ZOHO_CATALOG_INFO")
        return catalog_info

    def get_table_metadata(self, database_name: str = None, force_lowercase_column_names=False) -> ZohoSchemaModel:
        """ a badly named function, which returns the metadata for all tables, not just one"""
        database_name = database_name or self.default_databasename
        catalog_info = self.get_database_catalog(database_name=database_name)
        table_metadata = self.process_table_meta_data(catalog_info,
                                                      force_lowercase_column_names=force_lowercase_column_names)
        return table_metadata

    def get_org_and_workspace_id(self,database_name:str=None)->tuple[str,str]:
        database_name = database_name or self.default_databasename
        workspaces_metadata = self.get_all_workspaces_metadata_api_v2()

        for workspace in workspaces_metadata["data"]["ownedWorkspaces"] + workspaces_metadata["data"][
            "sharedWorkspaces"]:
            if workspace["workspaceName"] == database_name:
                workspace_id = workspace["workspaceId"]
                org_id = workspace["orgId"]
                return org_id,workspace_id
        else:
            raise "workspace not found"

    def get_table_metadata_v2(self, database_name: str = None, force_lowercase_column_names=False) -> ZohoSchemaModel_v2:
        """ Use the v2 API to get table metadata but return it in a similar data structure as the v1 function"""

        org_id, workspace_id = self.get_org_and_workspace_id(database_name=database_name)

        tables_data = self.get_views_api_v2(org_id=org_id, workspace_id=workspace_id,
                                                                      view_types=[0])
        table_catalog:dict[str,TableView_v2] = {}
        table_views = []
        for table in tables_data["data"]["views"]:
            view_id = table["viewId"]
            table_details = self.get_view_details_api_v2(view_id=view_id)
            table = table_details["data"]["views"]
            table_catalog[table["viewName"]] = TableView_v2(columns=table["columns"], tableName=table["viewName"],
                                                            tableType=table["viewType"], viewID=table["viewId"])

        table_metadata = self.process_table_meta_data_v2(catalog=table_catalog,
                                                      force_lowercase_column_names=force_lowercase_column_names)
        return table_metadata


    def create_table(self, table_design, database_name=None) -> MutableMapping:
        """
        ZOHO_DATATYPE
            (Supported data types are:
            PLAIN
            MULTI_LINE
            EMAIL
            NUMBER
            POSITIVE_NUMBER
            DECIMAL_NUMBER
            CURRENCY
            PERCENT
            DATE
            BOOLEAN
            URL
            AUTO_NUMBER
        """
        db_uri = self.getDBURI(self.login_email_id, database_name or self.default_databasename)
        columns = table_design['COLUMNS']
        BIG_NUMBER_OF_COLUMNS = 10
        if len(columns) < BIG_NUMBER_OF_COLUMNS:  # too many columns and zoho rejects the very long URL
            result = super().createTable(dbURI=db_uri, tableDesign=json.dumps(table_design))
        else:
            columns_initial, columns_residual = columns[:BIG_NUMBER_OF_COLUMNS], columns[BIG_NUMBER_OF_COLUMNS:]
            table_design['COLUMNS'] = columns_initial
            table_name = table_design['TABLENAME']
            result = super().createTable(dbURI=db_uri, tableDesign=json.dumps(table_design))
            time.sleep(1)
            uri_addcol = self.getURI(self.login_email_id, database_name or self.default_databasename,
                                     tableOrReportName=table_name)
            for col in columns_residual:
                self.addColumn(tableURI=uri_addcol, columnName=col['COLUMNNAME'], dataType=col['DATATYPE'])
                time.sleep(1)

        return result

    def create_table_v2(self, table_design:AnalyticsTableZohoDef_v2, database_name:str=None) -> MutableMapping:
        """
        ZOHO_DATATYPE
            (Supported data types are:
            PLAIN
            MULTI_LINE
            EMAIL
            NUMBER
            POSITIVE_NUMBER
            DECIMAL_NUMBER
            CURRENCY
            PERCENT
            DATE
            BOOLEAN
            URL
            AUTO_NUMBER
        """
        org_id, workspace_id = self.get_org_and_workspace_id(database_name=database_name)
        columns = table_design['COLUMNS']
        BIG_NUMBER_OF_COLUMNS = 10
        if len(columns) < BIG_NUMBER_OF_COLUMNS:
            result = super().createTable_v2(org_id=org_id,workspace_id=workspace_id,tableDesign=table_design)
        else:
            columns_initial, columns_residual = columns[:BIG_NUMBER_OF_COLUMNS], columns[BIG_NUMBER_OF_COLUMNS:]
            table_design['COLUMNS'] = columns_initial
            result = super().createTable_v2(org_id=org_id, workspace_id=workspace_id, tableDesign=table_design)
            new_table_id = result["data"]["viewId"]
            time.sleep(1)

            for col in columns_residual:
                self.addColumn_v2(org_id=org_id,workspace_id=workspace_id,view_id=new_table_id,column_def=col)

        return result

    def data_upload(self, import_content: str, table_name: str, import_mode="TRUNCATEADD",
                    matching_columns: Optional[str] = None,
                    database_name: Optional[str] = None,
                    retry_limit=None,
                    date_format=None) -> Optional[report_client.ImportResult]:
        """ data is a csv-style string, newline separated. Matching columns is a comma separated string
        import_mode is one of TRUNCATEADD, APPEND, UPDATEADD
        """
        retry_count = 0
        retry_limit = retry_limit or self.default_retries
        impResult = None
        # import_content_demojized = emoji.demojize(import_content)
        import_content_demojized = import_content  # try without this, move data cleaning to the calling function
        database_name = database_name or self.default_databasename
        uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name, tableOrReportName=table_name)
        # import_modes = APPEND / TRUNCATEADD / UPDATEADD
        impResult = self.importData_v1a(uri, import_mode=import_mode, import_content=import_content_demojized,
                                        date_format=date_format,
                                        matching_columns=matching_columns, retry_countdown=retry_limit)

        return impResult

    def data_export_using_sql(self, sql, table_name, database_name: str = None, cache_object=None,
                              cache_timeout_seconds=60, retry_countdown=5) -> csv.DictReader:
        """ returns a csv.DictReader after querying with the sql provided.
        retry_countdown is the number of retries
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
            callback_data = self.exportDataUsingSQL_v2(tableOrReportURI=uri, format='CSV', sql=sql,
                                                       retry_countdown=retry_countdown)
            returned_data = callback_data.getvalue().decode('utf-8-sig').splitlines()
            if cache_object:
                cache_object.set(sql, returned_data, cache_timeout_seconds)

        reader = csv.DictReader(returned_data)
        return reader

    def delete_rows(self, table_name, sql, database_name: Optional[str] = None, retry_countdown=5) -> int:
        """ criteria is SQL fragments such as 'a' in ColA, for example,
        sql = f"{id_column} IN ('ce76dc3a-bac0-47dd-841a-70e66613958e')
        return the count of eows
        """

        if len(sql) > 5000:
            raise RuntimeError("The SQL passed to delete_rows is too big and will cause Zoho 400 errors")
        uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name or self.default_databasename,
                          tableOrReportName=table_name)
        row_count = self.deleteData(tableURI=uri, criteria=sql, retry_countdown=retry_countdown)
        return row_count

    def pre_delete_rows(self, table_name, sql, database_name: Optional[str] = None, retry_countdown=5)->int:
        """ uses the same sql input as delete_rows and counts what is present in the table. This is to check the nbr of rows deleted is correct.
        Zoho sometimes gets table corruption which means rows don't delete.
        When the operation is critical, you can use this function to check the nbr of rows deleted is correct.
        """

        if len(sql) > 5000:
            raise RuntimeError("The SQL passed to delete_rows is too big and will cause Zoho 400 errors")
        sql = f"select count(*) from {table_name} where {sql}"
        reader = self.data_export_using_sql(sql, table_name=table_name)
        result = list(reader)[0]
        try:
            row_count = int(result['count(*)'])
        except KeyError:
            raise RuntimeError(f"Zoho returned unexpected data, did not found (count(8)) in the result: {result}")
        return row_count

    def rename_column(self, table_name, old_column_name, new_column_name, database_name: Optional[str] = None,
                      retry_countdown=5):
        """ rename a column in a table """
        uri = self.getURI(dbOwnerName=self.login_email_id, dbName=database_name or self.default_databasename,
                          tableOrReportName=table_name)
        self.renameColumn(tableURI=uri, oldColumnName=old_column_name, newColumnName=new_column_name,
                          retry_countdown=retry_countdown)
