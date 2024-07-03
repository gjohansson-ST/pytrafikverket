"""Filters and sorting for Trafikverket API requests."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import StrEnum
from typing import Any

from lxml import etree


class FilterOperation(StrEnum):
    """Contains all field filter operations."""

    EQUAL = "EQ"
    EXISTS = "EXISTS"
    GREATER_THAN = "GT"
    GREATER_THAN_EQUAL = "GTE"
    LESS_THAN = "LT"
    LESS_THAN_EQUAL = "LTE"
    NOT_EQUAL = "NE"
    LIKE = "LIKE"
    NOT_LIKE = "NOTLIKE"
    #    IN = "IN"  # noqa: ERA001
    NOT_IN = "NOTIN"  # codespell:ignore
    WITH_IN = "WITHIN"


class SortOrder(StrEnum):
    """Specifies how rows of data are sorted."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class FieldSort:
    """What field and how to sort on it."""

    def __init__(self, field: str, sort_order: SortOrder) -> None:
        """Initialize the class."""
        self._field = field
        self._sort_order = sort_order

    def to_string(self) -> str:
        """Sort_order as string."""
        return self._field + " " + self._sort_order.value


class Filter:
    """Base class for all filters."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_node(self, parent_node: etree._Element) -> Any:
        """Generate node."""


class FieldFilter(Filter):
    """Used to filter on one field."""

    def __init__(self, operation: FilterOperation, name: str, value: Any) -> None:
        """Initialize the class."""
        self.operation = operation
        self.name = name
        self.value = value

    def generate_node(self, parent_node: etree._Element) -> Any:
        """Return element node for field filter."""
        filter_node: etree._Element = etree.SubElement(
            parent_node, self.operation.value
        )
        filter_node.attrib["name"] = self.name
        filter_node.attrib["value"] = self.value
        return filter_node


class OrFilter(Filter):
    """Used to create a Or filter."""

    def __init__(self, filters: list[Filter]) -> None:
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node: Any) -> Any:
        """Return element node for filter."""
        or_node: etree._Element = etree.SubElement(parent_node, "OR")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node


class AndFilter(Filter):
    """Used to create a And filter."""

    def __init__(self, filters: list[Filter]) -> None:
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node: Any) -> etree._Element:
        """Return element node for filter."""
        or_node: etree._Element = etree.SubElement(parent_node, "AND")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node
