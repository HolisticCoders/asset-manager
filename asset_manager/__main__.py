import sys

import qdarkstyle

from PySide2.QtWidgets import QApplication
from asset_manager.ui.window import AssetManagerWindow


def main():
    app = QApplication(sys.argv)

    window = AssetManagerWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
