import logging

from PySide2 import QtWidgets

from asset_manager.api.config import user_settings, set_user_settings


logger = logging.getLogger(__name__)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle("Settings")

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(layout)
        path_label = QtWidgets.QLabel("Location")
        layout.addWidget(path_label)
        self.path_line_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.path_line_edit)
        path_button = QtWidgets.QPushButton("Browse")
        layout.addWidget(path_button)
        path_button.released.connect(self.browse_path)

        layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(layout)
        ok_button = QtWidgets.QPushButton("OK")
        layout.addWidget(ok_button)
        ok_button.released.connect(self.save_and_close)
        cancel_button = QtWidgets.QPushButton("Cancel")
        layout.addWidget(cancel_button)
        cancel_button.released.connect(self.close)
        apply_button = QtWidgets.QPushButton("Apply")
        layout.addWidget(apply_button)
        apply_button.released.connect(self.save_settings)
    
        self.load_settings()

    def apply(self):
        set_user_settings(self.settings)

    def browse_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory()
        if path:
            self.path_line_edit.setText(path)
        else:
            logger.info("Cancelled path browsing")
    
    def load_settings(self):
        self.settings = user_settings()
        self.path_line_edit.setText(self.settings["Download Directory"])

    def save_settings(self):
        self.settings["Download Directory"] = self.path_line_edit.text()
        set_user_settings(self.settings)

    def save_and_close(self):
        self.save_settings()
        self.close()
