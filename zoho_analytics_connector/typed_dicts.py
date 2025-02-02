from typing import TypedDict, Optional

class ColumnMetadata(TypedDict):
    """
    A TypedDict representing the metadata of a database column.
    """
    columnFormula: Optional[str]
    columnName: str
    columnSize: int
    dataType: str
    dateFormat: Optional[str]
    decimalDigits: int
    nullable: bool
    ordinalPosition: int
    pkcolumnName: Optional[str]
    pktableName: Optional[str]
    remarks: str
    typeName: str

ColumnName = str
TableName = str
ZohoTableModel = dict[ColumnName, ColumnMetadata]
ZohoSchemaModel =  dict[TableName, ZohoTableModel]