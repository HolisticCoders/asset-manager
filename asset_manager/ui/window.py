from PySide2.QtWidgets import QMainWindow, QTreeView
from asset_manager.api.asset import AssetModel
from asset_manager.api.auth import connect_to_google_drive

ROOT_ID = "TO_BE_FILLED"


class AssetManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Manager")
        self.tree_view = QTreeView()
        self.setCentralWidget(self.tree_view)
        google_drive = connect_to_google_drive()
        model = AssetModel(google_drive, [ROOT_ID])
        self.tree_view.setModel(model)
        self.tree_view.header().hide()


