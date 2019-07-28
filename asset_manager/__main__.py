import sys

from PySide2.QtWidgets import QApplication
from asset_manager.ui.window import AssetManagerWindow


def main():
    app = QApplication(sys.argv)

    window = AssetManagerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
