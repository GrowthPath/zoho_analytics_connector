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
