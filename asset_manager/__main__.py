import sys

import qdarkstyle
import qtmodern.styles
import qtmodern.windows

from PySide2.QtWidgets import QApplication
from asset_manager.ui.window import AssetManagerWindow


def main():
    app = QApplication(sys.argv)

    window = AssetManagerWindow()

    # use qdarkstyle stylesheet
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyside2())

    # Use QTDark theme
    # stylesheet = "asset_manager/QTDark.stylesheet"
    # with open(stylesheet, "r") as f:
    #     app.setStyleSheet(f.read())

    window.show()

    # Use Qtmodern stylesheet
    # qtmodern.styles.dark(app)
    # mw = qtmodern.windows.ModernWindow(window)
    # mw.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
