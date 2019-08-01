import logging
import os
from typing import List

from PySide2.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile, FileNotDownloadableError

from .config import user_settings
from .files import list_children


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Item:
    def __init__(
        self,
        row: int = 0,
        column: int = 0,
        google_file: GoogleDriveFile = None,
        parent=None,
    ) -> None:
        self.row = row
        self.column = column
        self.parent: Item = parent
        self.children: List[Item] = []
        self.google_file = google_file

    @property
    def disk_path(self) -> str:
        download_dir = user_settings()["Download Directory"]
        path_items = [self.name]

        last_parent = self
        while True:
            parent = last_parent.parent
            last_parent = parent
            if parent == None:
                break
            path_items.insert(0, parent.name)

        return os.path.join(download_dir, *path_items)

    @property
    def name(self) -> str:
        return self.google_file["title"]

    def download(self):
        logger.info(f"Downlading {self.name}")
        self.google_file.FetchMetadata()
        mimetype = self.google_file["mimeType"]
        try:
            directory = os.path.dirname(self.disk_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.google_file.GetContentFile(filename=self.disk_path, mimetype=mimetype)
        except FileNotDownloadableError:
            logger.warning(f"Couldn't download {self.name}")

        for child in self.children:
            child.download()

class AssetModel(QAbstractItemModel):
    asset_column_names = ["name", "id"]

    def __init__(
        self, google_drive: GoogleDrive, root_ids: List[str], parent: QObject = None
    ):
        super().__init__(parent)
        self.google_drive = google_drive
        self.root_ids = root_ids
        self.root_items: List[Item] = []
        self.create_item_tree()

    def create_item_tree(self):
        for root_row, root_id in enumerate(self.root_ids):
            root_file = self.google_drive.CreateFile({"id": root_id})
            root_file.FetchMetadata()
            root_item = Item(root_row, google_file=root_file)
            self.root_items.append(root_item)
            categories = list_children(self.google_drive, root_id)

            for category_row, category in enumerate(categories):
                category_item = Item(
                    category_row, parent=root_item, google_file=category
                )
                root_item.children.append(category_item)
                assets = list_children(self.google_drive, category["id"])

                for asset_row, asset in enumerate(assets):
                    asset_item = Item(asset_row, parent=category_item, google_file=asset)
                    category_item.children.append(asset_item)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not parent.isValid():
            item = self.root_items[row]
        elif not parent.parent().isValid():
            root_item = self.root_items[parent.row()]
            item = root_item.children[row]
        else:
            root_item = self.root_items[parent.parent().row()]
            category_item = root_item.children[parent.row()]
            item = category_item.children[row]

        return self.createIndex(row, column, item)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        if item in self.root_items:
            return QModelIndex()

        parent = item.parent
        if parent is None:
            return QModelIndex()
        else:
            return self.createIndex(parent.row, parent.column, parent)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return len(self.root_ids)
        item = parent.internalPointer()
        return len(item.children)


    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            return 1
        if not parent.parent().isValid():
            return 1

        return len(AssetModel.asset_column_names)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        if not index.isValid():
            return

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            if index.column() == 0:

                return item.google_file.metadata.get("title", "CONTACT SUPPORT SHIT IS BROKEN")

