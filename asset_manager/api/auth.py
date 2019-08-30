import os

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from .config import credentials_path, client_secrets_path


def connect_to_google_drive() -> GoogleDrive:
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(client_secrets_path())
    # Try to load saved client credentials
    credentials_file = credentials_path()
    gauth.LoadCredentialsFile(credentials_file)
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile(credentials_file)

    return GoogleDrive(gauth)
