import logging
from typing import List

from PySide2 import QtCore, QtGui, QtWidgets

from asset_manager.api.item import ItemModel, Item
from asset_manager.api.auth import connect_to_google_drive
from asset_manager.api.config import FOLDER_IDS, user_settings
from asset_manager.ui.settings import SettingsDialog

logger = logging.getLogger(__name__)


class AssetManagerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")

        settings_action = QtWidgets.QAction("&Open Settings", self)
        settings_action.triggered.connect(self.open_settings)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(settings_action)

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_menu)
        self.setCentralWidget(self.tree_view)
        google_drive = connect_to_google_drive()
        model = ItemModel(google_drive, FOLDER_IDS)
        self.tree_view.setModel(model)
        self.tree_view.header().hide()

    def open_settings(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def open_menu(self, position):
        menu = QtWidgets.QMenu()
        download_action = menu.addAction("Download")
        download_action.triggered.connect(self.download)
        upload_action = menu.addAction("Upload")
        upload_action.triggered.connect(self.upload)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def download(self):
        logger.info("Downloading")
        items = self._get_selected_items()
        if self._is_local_folder_modified(items):
            button = QtWidgets.QMessageBox.question(
                self,
                "Download Files",
                "You have modifications on your local files, "
                "do you want to override them?",
            )
            if button != QtWidgets.QMessageBox.Yes:
                return
        for item in items:
            item.download()

    def upload(self, folder_name):
        logger.warning("Uploading")
        items: List[Item] = [
            f.internalPointer() for f in self.tree_view.selectedIndexes()
        ]
        for item in items:
            item.upload()

    def _get_selected_items(self) -> List[Item]:
        return [f.internalPointer() for f in self.tree_view.selectedIndexes()]

    @staticmethod
    def _is_local_folder_modified(folders: List[Item]) -> bool:
        def _check_modifications_recursively(folder: Item) -> bool:
            if folder.status == Item.Status.ModifiedLocally:
                return True
            for child in folder.children:
                if _check_modifications_recursively(child):
                    return True
            return False

        for folder in folders:
            if _check_modifications_recursively(folder):
                return True

            return False

