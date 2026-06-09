# Manages currently selected component state for the operator UI
from typing import Optional
from models.component import Component
from csc_01_component_db.csu_01_component_data_loader import get_component_loader


class ComponentSelector:
    def __init__(self):
        self._loader = get_component_loader()
        self._selected_id: Optional[str] = None

    def select(self, component_id: str) -> Optional[Component]:
        comp = self._loader.get_by_id(component_id)
        if comp:
            self._selected_id = component_id
        return comp

    def get_selected(self) -> Optional[Component]:
        if self._selected_id is None:
            return None
        return self._loader.get_by_id(self._selected_id)

    def get_selected_id(self) -> Optional[str]:
        return self._selected_id

    def get_all_components(self):
        return self._loader.get_all()

    def clear(self):
        self._selected_id = None
