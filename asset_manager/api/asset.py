import logging
import os
from datetime import datetime
from typing import List

from PySide2.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile, FileNotDownloadableError

from .config import user_settings
from .files import list_children


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GOOGLE_DRIVE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Item:
    def __init__(
        self,
        row: int = 0,
        column: int = 0,
        google_file: GoogleDriveFile = None,
        parent=None,
        google_drive: GoogleDrive = None,
        disk_path: str = "",
    ) -> None:
        self.row = row
        self.column = column
        self.parent_item: Item = parent
        self.children: List[Item] = []
        self.google_file = google_file
        self.google_drive = google_drive
        self._disk_path = disk_path

    def __eq__(self, other):
        return self.disk_path == other.disk_path

    @property
    def disk_path(self) -> str:
        if not self._disk_path:
            self._disk_path = self._derive_path_from_parents()
        return self._disk_path

    @property
    def ordered_children(self) -> List[Item]:
        return sorted(self.children, key=lambda item:item.name)
    
    @property
    def is_local(self):
        return os.path.exists(self.disk_path)
    
    @property
    def is_remote(self):
        return self.google_file is not None
    
    @property
    def remote_datetime(self):
        return datetime.strptime(
            self.google_file["modifiedDate"], GOOGLE_DRIVE_DATETIME_FORMAT
        )

    @property
    def local_datetime(self):
        return datetime.fromtimestamp(
            os.path.getmtime(self.disk_path)
        )

    def _derive_path_from_parents(self):
        download_dir = user_settings()["Download Directory"]
        path_items = [self.name]

        last_parent = self
        while True:
            parent = last_parent.parent_item
            last_parent = parent
            if parent == None:
                break
            path_items.insert(0, parent.name)

        return os.path.expandvars(
            os.path.expanduser(os.path.join(download_dir, *path_items))
        )

    @property
    def name(self) -> str:
        return os.path.basename(self.disk_path)

    def is_local_more_recent(self) -> bool:
        if self.is_local:
            return False
        if self.remote_datetime < self.local_datetime:
            return True
        return False

    def download(self):
        logger.info(f"Downlading {self.name}")
        self.google_file.FetchMetadata()
        mimetype = self.google_file["mimeType"]
        try:
            directory = os.path.dirname(self.disk_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.google_file.GetContentFile(filename=self.disk_path, mimetype=mimetype)
        except KeyError:
            logger.error(
                "Please set the Download Directory in the File > Open Settings window."
            )
            return
        except FileNotDownloadableError:
            logger.warning(f"Couldn't download {self.name}")

        for child in self.children:
            child.download()

    def upload(self):
        logger.warning(f"Uploading {self.name}")
        if os.path.exists(self.disk_path):
            self.google_file.SetContentFile(self.disk_path)
            self.google_file.Upload()


class AssetModel(QAbstractItemModel):
    asset_column_names = ["name", "id"]

    def __init__(
        self, google_drive: GoogleDrive, root_ids: List[str], parent: QObject = None
    ):
        super().__init__(parent)
        self.google_drive = google_drive
        self.root_ids = root_ids
        self.root_items: List[Item] = []

        # self.remote_root_items: List[Item] = []
        # self.create_remote_item_tree()

        self.local_root_items: List[Item] = []
        self.create_local_item_tree()

    def create_remote_item_tree(self):
        for root_row, root_id in enumerate(self.root_ids):
            root_file = self.google_drive.CreateFile({"id": root_id})
            root_file.FetchMetadata()
            root_item = Item(
                root_row, google_file=root_file, google_drive=self.google_drive
            )
            self.remote_root_items.append(root_item)
            self._create_remote_children_recursively(root_item)

    def _create_remote_children_recursively(self, parent_item: Item):
        drive_children = list_children(self.google_drive, parent_item.google_file["id"])
        for row, child in enumerate(drive_children):
            item = Item(
                row,
                parent=parent_item,
                google_file=child,
                google_drive=self.google_drive,
            )
            parent_item.children.append(item)
            self._create_remote_children_recursively(item)

    def create_local_item_tree(self):
        download_dir = user_settings()["Download Directory"]
        for root, folders, files in os.walk(download_dir):
            for root_row, root_folder in enumerate(folders):
                root_folder = os.path.join(root, root_folder)
                root_item = Item(root_row, disk_path=root_folder)
                self.local_root_items.append(root_item)
                self._create_local_children_recursively(root_item)

    def _create_local_children_recursively(self, parent_item: Item):
        elements = sorted(os.listdir(parent_item.disk_path))
        for row, element in enumerate(elements):
            path = os.path.join(parent_item.disk_path, element)
            item = Item(row, parent=parent_item, disk_path=path)

            parent_item.children.append(item)

            if os.path.isdir(path):
                self._create_local_children_recursively(item)

    def merge_local_and_remote_trees(self):
        local = self.local_root_items
        remote = self.remote_root_items

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not parent.isValid():
            item = self.local_root_items[row]
        else:
            item = parent.internalPointer().children[row]
        return self.createIndex(row, column, item)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        if item in self.local_root_items:
            return QModelIndex()

        parent = item.parent_item
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
                return item.name
                # return item.google_file.metadata.get(
                #     "title", "CONTACT SUPPORT SHIT IS BROKEN"
                # )
