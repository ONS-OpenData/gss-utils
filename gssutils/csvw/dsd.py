from typing import NamedTuple, Union, List, Optional

from gssutils.csvw.namespaces import URI


class Resource(NamedTuple):
    at_id: URI
    at_type: Union[None, URI, List[URI]] = None


class DimensionProperty(NamedTuple):
    at_id: URI
    at_type: Union[URI, List[URI]] = "qb:DimensionProperty"
    qb_codeList: Optional[Resource] = None
    rdfs_range: Optional[Resource] = None


class MeasureProperty(NamedTuple):
    at_id: URI
    at_type: Union[URI, List[URI]] = "qb:MeasureProperty"
    rdfs_range: Optional[Resource] = None


class AttributeProperty(NamedTuple):
    at_id: URI
    at_type: Union[URI, List[URI]] = "qb:AttributeProperty"
    rdfs_range: Optional[Resource] = None


class DimensionComponent(NamedTuple):
    at_id: URI
    qb_dimension: DimensionProperty
    at_type: Union[URI, List[URI]] = "qb:ComponentSpecification"
    qb_componentProperty: Optional[Resource] = None


class MeasureComponent(NamedTuple):
    at_id: URI
    qb_measure: MeasureProperty
    at_type: Union[URI, List[URI]] = "qb:ComponentSpecification"
    qb_componentProperty: Optional[Resource] = None


class AttributeComponent(NamedTuple):
    at_id: URI
    qb_attribute: AttributeProperty
    at_type: Union[URI, List[URI]] = "qb:ComponentSpecification"
    qb_componentProperty: Optional[Resource] = None
    qb_componentRequired: Optional[bool] = None


Component = Union[DimensionComponent, MeasureComponent, AttributeComponent]


class DSD(NamedTuple):
    at_id: URI = '#structure'
    at_type: Union[URI, List[URI]] = "qb:DataStructureDefinition"
    qb_component: List[Union[DimensionComponent, MeasureComponent, AttributeComponent]] = []


class DataSet(NamedTuple):
    at_id: URI = '#dataset'
    at_type: Union[URI, List[URI]] = ["qb:DataSet", "dcat:Dataset"]
    qb_structure: DSD = DSD()