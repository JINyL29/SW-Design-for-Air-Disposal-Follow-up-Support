# Loads component specifications from JSON and builds Component instances
import json
import os
from typing import Dict, List, Optional
from models.component import Component

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'component_voltage_db.json')
_instance: Optional['ComponentDataLoader'] = None


def get_component_loader() -> 'ComponentDataLoader':
    global _instance
    if _instance is None:
        _instance = ComponentDataLoader()
        _instance.load()
    return _instance


class ComponentDataLoader:
    def __init__(self, path: str = _DATA_PATH):
        self._path = path
        self._components: Dict[str, Component] = {}

    def load(self) -> Dict[str, Component]:
        with open(self._path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data['components']:
            comp = Component(
                id=item['id'],
                name=item['name'],
                model_name=item['model_name'],
                voltage_min=item['critical_low'],
                voltage_max=item['normal_max'],
                voltage_warn_low=item['critical_low'],
                voltage_warn_high=item['normal_min'],
                priority=item['priority'],
                has_ov_critical=item.get('has_ov_critical', False),
            )
            self._components[comp.id] = comp
        return self._components

    def get_all(self) -> List[Component]:
        if not self._components:
            self.load()
        return sorted(self._components.values(), key=lambda c: c.priority)

    def get_by_id(self, component_id: str) -> Optional[Component]:
        if not self._components:
            self.load()
        return self._components.get(component_id)
