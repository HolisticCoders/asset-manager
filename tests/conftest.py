from pytest import fixture
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


@fixture(scope="session")
def google_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    return GoogleDrive(gauth)
