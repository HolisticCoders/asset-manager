import logging
import hashlib
import os
import pdb
from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import List


from PySide2.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt
from PySide2.QtGui import QBrush, QColor

from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile, FileNotDownloadableError

from .config import ITEM_STATE_COLORS, user_settings
from .files import list_children


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GOOGLE_DRIVE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Item:
    class Status(Enum):
        RemoteOnly = "remote-only"
        Synced = "synced"
        LocalOnly = "local-only"
        ModifiedLocally = "modified-locally"
        DeletedLocally = "deleted-locally"
        ModifiedRemotely = "modified-remotely"
        DeletedRemotely = "deleted-remotely"

    class Kind(Enum):
        Remote = "remote"
        Local = "local"

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
    def ordered_children(self):
        return sorted(self.children, key=lambda item: item.name)

    @property
    def is_local(self):
        return os.path.exists(self.disk_path)

    @property
    def is_remote(self):
        return self.google_file is not None

    @property
    def status(self):
        if self.is_local and not self.is_remote:
            return Item.Status.LocalOnly
        elif self.is_remote and not self.is_local:
            return Item.Status.RemoteOnly
        else:
            more_recent = self.get_more_recent()
            if more_recent and self.is_content_modified():
                if more_recent == Item.Kind.Remote:
                    return Item.Status.ModifiedRemotely
                else:
                    return Item.Status.ModifiedLocally
        return Item.Status.Synced

    @property
    def remote_datetime(self):
        return datetime.strptime(
            self.google_file["modifiedDate"], GOOGLE_DRIVE_DATETIME_FORMAT
        )

    @property
    def local_datetime(self):
        return datetime.fromtimestamp(os.path.getmtime(self.disk_path))

    def _derive_path_from_parents(self):
        download_dir = user_settings()["Download Directory"]
        path_items = [self.name]

        last_parent = self
        while True:
            parent = last_parent.parent_item
            last_parent = parent
            if not parent:
                break
            path_items.insert(0, parent.name)

        return os.path.expandvars(
            os.path.expanduser(os.path.join(download_dir, *path_items))
        )

    @property
    def name(self) -> str:
        if self.google_file:
            return self.google_file["title"]
        return os.path.basename(self.disk_path)

    def is_local_more_recent(self) -> bool:
        if not self.is_local:
            return False
        if self.remote_datetime < self.local_datetime:
            return True
        return False

    def get_more_recent(self):
        if self.is_local and not self.is_remote:
            return Item.Kind.Local
        elif self.is_remote and not self.is_local:
            return Item.Kind.Remote
        else:
            if self.remote_datetime < self.local_datetime:
                return Item.Kind.Local
            elif self.local_datetime < self.remote_datetime:
                return Item.Kind.Remote
        return None

    def is_content_modified(self) -> bool:
        if not self.is_local or not self.is_remote:
            return False
        if not os.path.isfile(self.disk_path):
            return False
        local_content = self._get_local_content_bytes()
        local_checksum = hashlib.md5(local_content).hexdigest()
        remote_checksum = self.google_file["md5Checksum"]
        return local_checksum != remote_checksum

    def is_local_modified(self) -> bool:
        if not os.path.isfile(self.disk_path):
            return False
        with open(self.disk_path, "r+") as handle:
            local_content = handle.read()
        remote_content = self.google_file.GetContentString()
        return local_content != remote_content

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

    def _get_local_content_bytes(self):
        try:
            with open(self.disk_path) as handle:
                return handle.read().encode()
        except UnicodeDecodeError:
            with open(self.disk_path, "rb") as handle:
                return handle.read()


class AssetModel(QAbstractItemModel):
    asset_column_names = ["name", "id"]

    def __init__(
        self, google_drive: GoogleDrive, root_ids: List[str], parent: QObject = None
    ):
        super().__init__(parent)
        self.google_drive = google_drive
        self.root_ids = root_ids
        self.root_items: List[Item] = []

        self.remote_root_items: List[Item] = []
        self.create_remote_item_tree()

        self.local_root_items: List[Item] = []
        self.create_local_item_tree()

        self.merge_local_and_remote_trees()

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
        self.root_items = deepcopy(self.remote_root_items)
        self.merge_trees_recursively(self.root_items, self.local_root_items)

    def merge_trees_recursively(self, items, local_items):
        def get_local_from_item(item):
            for local_item in local_items:
                if item == local_item:
                    return local_item

        for item in items:
            local_item = get_local_from_item(item)
            if not local_item:
                continue

            for local_child in local_item.children:
                if local_child not in item.children:
                    item.children.append(local_child)
                    local_child.parent_item = item
                    local_child.row = len(item.children) - 1

            self.merge_trees_recursively(item.children, local_item.children)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if not parent.isValid():
            item = self.root_items[row]
        else:
            item = parent.internalPointer().children[row]
        return self.createIndex(row, column, item)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        item = index.internalPointer()
        if item in self.root_items:
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
        if role == Qt.ForegroundRole:
            if index.column() == 0:
                status = item.status.value
                color = QColor(ITEM_STATE_COLORS[status])
                return QBrush(color)
