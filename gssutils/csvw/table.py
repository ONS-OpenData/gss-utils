from typing import NamedTuple, Optional, Union, List

from gssutils.csvw.namespaces import URI


class Datatype(NamedTuple):
    base: Optional[str] = None
    format: Optional[str] = None


class Column(NamedTuple):
    name: str
    titles: Union[str, List[str], None] = None
    datatype: Union[str, Datatype, None] = None
    suppressOutput: Optional[bool] = None
    virtual: Optional[bool] = None
    required: Optional[bool] = None
    propertyUrl: Optional[URI] = None
    valueUrl: Optional[URI] = None


class ColumnReference(NamedTuple):
    resource: str
    columnReference: str


class ForeignKey(NamedTuple):
    columnReference: str
    reference: ColumnReference


class TableSchema(NamedTuple):
    columns: List[Column]
    primaryKey: Optional[list] = None
    foreignKeys: Optional[List[ForeignKey]] = None
    aboutUrl: Optional[URI] = None


class Table(NamedTuple):
    url: str
    tableSchema: Union[str, TableSchema]
    suppressOutput: Optional[bool] = None