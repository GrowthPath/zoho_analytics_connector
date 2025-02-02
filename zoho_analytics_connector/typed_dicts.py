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


class TableMetadata(TypedDict):
    """
    A TypedDict representing the metadata of a database table.

    The keys are the column names and the values are the column's metadata.
    """

    # The [str, ColumnMetadata] indicates a dictionary with string keys, and columnMetadata values.
    # This matches the way TypedDicts are used and ensures type checking during access.
    # we use a dictionary to map column names to metadata.
    __root__: dict[str, ColumnMetadata]


class SchemaMetadata(TypedDict):
    __root__: dict[str, TableMetadata]