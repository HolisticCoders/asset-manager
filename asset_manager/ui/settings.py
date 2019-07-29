from PySide2 import QtWidgets

from asset_manager.api.config import user_settings, set_user_settings


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self):
        self.settings = user_settings()
        self.setModal(True)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        layout = QtWidgets.QHBoxLayout()
        main_layout = QtWidgets.addLayout(layout)
        label = QtWidgets.QLabel("Location")
        layout.add

    def apply(self):
        set_user_settings(self.settings)
