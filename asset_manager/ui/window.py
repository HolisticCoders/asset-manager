import logging
import subprocess
import webbrowser
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
        selected_item = self._get_selected_item()

        download_action = menu.addAction("Download")
        download_action.triggered.connect(self.download)

        upload_action = menu.addAction("Upload")
        upload_action.triggered.connect(self.upload)

        open_explorer_action = menu.addAction("Open In Explorer")
        open_explorer_action.triggered.connect(self.open_in_explorer)


        open_drive_action = menu.addAction("Open On Google Drive")
        open_drive_action.triggered.connect(self.open_on_drive)

        if not selected_item.is_local:
            upload_action.setEnabled(False)
            open_explorer_action.setEnabled(False)

        if not selected_item.is_remote:
            download_action.setEnabled(False)
            open_drive_action.setEnabled(False)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def download(self):
        logger.info("Downloading")
        item = self._get_selected_item()
        if self._is_local_folder_modified(item):
            button = QtWidgets.QMessageBox.question(
                self,
                "Download Files",
                "You have modifications on your local files, "
                "do you want to override them?",
            )
            if button != QtWidgets.QMessageBox.Yes:
                return
        item.download()

    def upload(self):
        logger.warning("Uploading")
        item = self._get_selected_item()
        item.upload()
    
    def open_in_explorer(self, *args, **kwargs):
        item = self._get_selected_item()
        if item.is_local:
            path = item.disk_path.replace('/', "\\")
            if item.is_file:
                command = f'explorer /select,"{path}"'
            else:
                command = f'explorer "{path}"'
            subprocess.Popen(command)

    def open_on_drive(self):
        item = self._get_selected_item()
        if item.is_remote:
            if not item.is_folder:
                item = item.parent_item
            webbrowser.open_new_tab(item.url)

    def _get_selected_items(self) -> List[Item]:
        return [f.internalPointer() for f in self.tree_view.selectedIndexes()]

    def _get_selected_item(self) -> Item:
        return self.tree_view.currentIndex().internalPointer()

    @staticmethod
    def _is_local_folder_modified(folder: Item) -> bool:
        def _check_modifications_recursively(folder: Item) -> bool:
            if folder.status == Item.Status.ModifiedLocally:
                return True
            for child in folder.children:
                if _check_modifications_recursively(child):
                    return True
            return False

        if _check_modifications_recursively(folder):
            return True

        return False

