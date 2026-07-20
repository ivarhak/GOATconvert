"""GOATconvert entrypoint. Fully offline — no network calls anywhere."""

import sys

from PySide6.QtWidgets import QApplication

from goatconvert.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
