from PySide2 import QtWidgets, QtCore

from asset_manager.api.asset import AssetModel
from asset_manager.api.config import FOLDER_IDS
from asset_manager.api.auth import connect_to_google_drive


class AssetManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")

        settings_action = QtWidgets.QAction("&Open Settings", self)
        settings_action.triggered.connect(self.open_settings)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(settings_action)

        self.tree_view = QtWidgets.QTreeView()
        self.setCentralWidget(self.tree_view)
        google_drive = connect_to_google_drive()
        model = AssetModel(google_drive, FOLDER_IDS)
        self.tree_view.setModel(model)
        self.tree_view.header().hide()

    def open_settings(self):
        print("OPENING SETTINGS DIALOG")
