from typing import TypedDict, List

from zoho_analytics_connector.zoho_analytics_connector.typed_dicts import DataTypeAddColumn


class LookupDef(TypedDict):
    child_column: str
    parent_column: str
    parent_table: str


class LookupDef_v2(TypedDict):
    TABLENAME: str
    COLUMNNAME: str


class ColumnDef(TypedDict):
    COLUMNNAME: str
    django_model_column_name: str
    DESCRIPTION: str
    MANDATORY: str
    DATATYPE: DataTypeAddColumn


class ColumnDef_v2(TypedDict):
    COLUMNNAME: str
    django_model_column_name: str  # zoho does not want to see this in the API
    DESCRIPTION: str
    MANDATORY: str
    DATATYPE: DataTypeAddColumn
    LOOKUPCOLUMN: LookupDef_v2


class AnalyticsTableZohoDef(TypedDict):
    TABLENAME: str
    TABLEDESCRIPTION: str
    FOLDERNAME: str
    LOOKUPS: List[LookupDef]
    COLUMNS: List[ColumnDef]


class AnalyticsTableZohoDef_v2(TypedDict):
    TABLENAME: str
    TABLEDESCRIPTION: str
    FOLDERNAME: str
    COLUMNS: List[ColumnDef_v2]


# this class is used by the original Dear Analytics, and replacing it with the abstract version causes migration nightmares


# --- Assumptions ---
# 1. AnalyticsTableDear and AnalyticsTableAbstract are independent base classes.
# 2. We want to find *any* concrete Django model that ultimately inherits
#    from EITHER base and has the analytics_table_name attribute.
# for backwards compatability, default the app_label_filter to dear_zoho_analytics


