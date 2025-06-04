from typing import TypedDict, Optional, Literal, NotRequired, Final

DataTypeCode = str
DataTypeName = Literal[
    "Plain Text",
    "Multi Line Text",
    "E-mail",
    "Number",
    "Positive Number",
    "Decimal Number",
    "Currency",
    "Percentage",
    "Date",
    "Yes/No Decision",
    "URL",
    "Auto Number"
]

# these are the values when adding a column
DataTypeAddColumn = Literal[
    "PLAIN",
    "MULTI_LINE",
    "EMAIL",
    "NUMBER",
    "POSITIVE_NUMBER",
    "DECIMAL_NUMBER",
    "CURRENCY",
    "PERCENT",
    "DATE",
    "BOOLEAN",
    "URL",
    "AUTO_NUMBER"
]

data_type_nbr_data_type_mapping: Final = {
    12: [s.strip() for s in "PLAIN / MULTI_LINE / EMAIL / URL".split('/')],
    -7: [s.strip() for s in "BOOLEAN".split('/')],
    8: [s.strip() for s in "PERCENT / CURRENCY / DECIMAL_NUMBER".split('/')],
    -5: [s.strip() for s in "NUMBER / AUTO_NUMBER / POSITIVE_NUMBER".split('/')],
    93: [s.strip() for s in "DATE".split('/')]  # Handles cases with no delimiter gracefully
}


class ColumnMetadata(TypedDict):
    """
    A TypedDict representing the metadata of a database column.
    """
    columnFormula: Optional[str]
    columnName: str
    columnSize: int
    dataType: DataTypeCode
    dateFormat: Optional[str]
    decimalDigits: int
    nullable: bool
    ordinalPosition: int
    pkcolumnName: Optional[str]
    pktableName: Optional[str]
    remarks: str
    typeName: DataTypeName


class ColumnMetadata_v2(TypedDict):
    """
    A TypedDict representing the metadata of a database column.
    """
    columnDesc: str
    columnId: str
    columnIndex: int
    columnMaxSize: int
    columnName: str
    dataType: DataTypeAddColumn
    dataTypeName: DataTypeCode
    dataTypeId: int
    defaultValue: str
    formulaDisplayName: str
    isNullable: bool
    pkColumnName: str
    pkTableName: str


class TableView(TypedDict, ):
    columns: list[ColumnMetadata]
    isfav: bool
    remarks: Optional[str]
    tableName: str
    tableType: str
    viewID: NotRequired[str]


class TableView_v2(TypedDict, ):
    columns: list[ColumnMetadata_v2]
    tableName: str
    tableType: str
    viewID: str


class Catalog(TypedDict):
    tableCat: str  # table name
    views: list[TableView]


ColumnName = str
TableName = str
ZohoTableModel = dict[ColumnName, ColumnMetadata]
ZohoSchemaModel = dict[TableName, ZohoTableModel]
ZohoTableModel_v2 = dict[ColumnName, ColumnMetadata_v2]
ZohoSchemaModel_v2 = dict[TableName, ZohoTableModel_v2]


class ZohoWorkspace(TypedDict):
    """TypedDict representing a single Zoho workspace's metadata."""
    createdBy: str  # Email address of the creator
    createdTime: str  # Timestamp string (e.g., "1740617804006") - Note: It's a string in the JSON
    isDefault: bool  # Whether this is the default workspace
    orgId: str  # Organization ID string (e.g., "629101756")
    workspaceDesc: str  # Workspace description (can be an empty string)
    workspaceId: str  # Workspace ID string (e.g., "1252003000007995001")
    workspaceName: str  # Name of the workspace (e.g., "NewWorkspace")


class ZohoWorkspaceData(TypedDict):
    """TypedDict representing the 'data' section of the workspace response."""
    ownedWorkspaces: list[ZohoWorkspace]
    sharedWorkspaces: list[ZohoWorkspace]


class ZohoWorkspacesResponse(TypedDict):
    """TypedDict representing the full response structure for getting all workspaces."""
    data: ZohoWorkspaceData
    status: str  # Status indicator (e.g., "success")
    summary: str  # Summary message (e.g., "Get all workspaces")
