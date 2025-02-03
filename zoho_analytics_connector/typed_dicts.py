from typing import TypedDict, Optional, Literal

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
    "Decision Box",
    "URL",
    "Auto Number"
]

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

class TableView(TypedDict):
    columns: list[ColumnMetadata]
    isfav: bool
    remarks: Optional[str]
    tableName: str
    tableType: str

class Catalog(TypedDict):
    tableCat: str
    views: list[TableView]

ColumnName = str
TableName = str
ZohoTableModel = dict[ColumnName, ColumnMetadata]
ZohoSchemaModel =  dict[TableName, ZohoTableModel]