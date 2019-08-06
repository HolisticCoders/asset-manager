from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFileList


def list_children(google_drive: GoogleDrive, parent_id: str) -> GoogleDriveFileList:
    metadata = {
        # "q": f"'{parent_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'",
        "q": f"'{parent_id}' in parents and trashed=false",
        "orderBy": "title",
    }
    return google_drive.ListFile(metadata).GetList()
