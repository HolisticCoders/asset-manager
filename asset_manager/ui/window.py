import logging
from typing import List

from PySide2 import QtCore, QtGui, QtWidgets

from asset_manager.api.asset import AssetModel, Item
from asset_manager.api.auth import connect_to_google_drive
from asset_manager.api.config import FOLDER_IDS
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
        model = AssetModel(google_drive, FOLDER_IDS)
        self.tree_view.setModel(model)
        self.tree_view.header().hide()

    def open_settings(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def open_menu(self, position):
        menu = QtWidgets.QMenu()
        download_action = menu.addAction("Download")
        download_action.triggered.connect(self.download_folders)
        upload_action = menu.addAction("Upload")
        upload_action.triggered.connect(self.upload_folders)

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def download_folders(self):
        logger.info("Downloading")
        folders: List[Item] = [f.internalPointer() for f in self.tree_view.selectedIndexes()]
        for folder in folders:
            folder.download()

    def upload_folders(self, folder_name):
        logger.info("Uploading")
        folders: List[Item] = [f.internalPointer() for f in self.tree_view.selectedIndexes()]
