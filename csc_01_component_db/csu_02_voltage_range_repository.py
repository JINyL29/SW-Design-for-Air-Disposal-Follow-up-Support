# Repository providing voltage range queries for components
from typing import Dict, Optional, Tuple
from models.component import Component
from csc_01_component_db.csu_01_component_data_loader import get_component_loader


class VoltageRangeRepository:
    def __init__(self, components: Optional[Dict[str, Component]] = None):
        if components is not None:
            self._components = components
        else:
            loader = get_component_loader()
            self._components = {c.id: c for c in loader.get_all()}

    def get_normal_range(self, component_id: str) -> Optional[Tuple[float, float]]:
        comp = self._components.get(component_id)
        if comp is None:
            return None
        return (comp.voltage_warn_high, comp.voltage_max)

    def get_warning_range(self, component_id: str) -> Optional[Tuple[float, float]]:
        comp = self._components.get(component_id)
        if comp is None:
            return None
        return (comp.voltage_min, comp.voltage_warn_high)

    def get_critical_low(self, component_id: str) -> Optional[float]:
        comp = self._components.get(component_id)
        return comp.voltage_min if comp else None

    def get_critical_high(self, component_id: str) -> Optional[float]:
        comp = self._components.get(component_id)
        if comp is None:
            return None
        return comp.voltage_max if comp.has_ov_critical else None

    def get_component(self, component_id: str) -> Optional[Component]:
        return self._components.get(component_id)

    def all_ids(self):
        return list(self._components.keys())
