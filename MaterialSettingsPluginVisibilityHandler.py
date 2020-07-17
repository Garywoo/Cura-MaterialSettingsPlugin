# Copyright (c) 2020 fieldOfView
# The MaterialSettingsPlugin is released under the terms of the AGPLv3 or higher.

from UM.Settings.Models.SettingVisibilityHandler import SettingVisibilityHandler
from UM.Settings.InstanceContainer import DefinitionNotFoundError

from cura.CuraApplication import CuraApplication
from cura.Machines.MaterialNode import MaterialNode

from UM.FlameProfiler import pyqtSlot

class MaterialSettingsPluginVisibilityHandler(SettingVisibilityHandler):
    def __init__(self, parent = None, *args, **kwargs):
        super().__init__(parent = parent, *args, **kwargs)

        self._selected_material_node = None
        self._last_material_node = self._selected_material_node
        self._last_visible_settings = set(self.getVisible())

        self.visibilityChanged.connect(self._onVisibilityChanged)

    def _onVisibilityChanged(self) -> None:
        if self._last_material_node != self._selected_material_node:
            self._last_visible_settings = set(self.getVisible())
            self._last_material_node = self._selected_material_node
            return

        new_visible_settings = set(self.getVisible())
        added_settings = new_visible_settings - self._last_visible_settings
        removed_settings = self._last_visible_settings - new_visible_settings
        self._last_visible_settings = new_visible_settings

        if not added_settings and not removed_settings:
            return

        base_file = self._selected_material_node.container.getMetaDataEntry("base_file")
        containers = CuraApplication.getInstance().getContainerRegistry().findInstanceContainers(base_file=base_file)

        for setting_key in removed_settings:
            for container in containers:
                container.removeInstance(setting_key)

        try:
            definition = self._selected_material_node.container.getDefinition()
        except DefinitionNotFoundError:
            Logger.log("w", "Tried to set value of setting when the container has no definition")
            return

        for setting_key in added_settings:
            setting_definition = definition.findDefinitions(key = setting_key)
            if not setting_definition:
                Logger.log("w", "Tried to set value of setting %s that has no instance in container %s or its definition %s", setting_key, container.getName(), definition.getName())
                return
            default_value = getattr(setting_definition[0], "default_value")

            for container in containers:
                definition = container.getDefinition()
                container.setProperty(setting_key, "value", default_value)

    @pyqtSlot("QVariant")
    def updateFromMaterialNode(self, material_node: MaterialNode) -> None:
        self._selected_material_node = material_node
        container = material_node.container
        if not container:
            return
        material_settings = set(container.getAllKeys())
        if material_settings != self.getVisible():
            self.setVisible(material_settings)

    ##  Set a single SettingDefinition's visible state
    @pyqtSlot(str, bool)
    def setSettingVisibility(self, key: str, visible: bool) -> None:
        visible_settings = self.getVisible()
        if visible:
            visible_settings.add(key)
        else:
            try:
                visible_settings.remove(key)
            except KeyError:
                pass

        self.setVisible(visible_settings)