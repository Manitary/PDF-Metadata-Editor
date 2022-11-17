import sys
import os
import logging
import argparse
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QMainWindow, QFileDialog, QFormLayout, QHBoxLayout, QMessageBox, QMenu
from PyQt6.QtGui import QAction, QActionGroup, QFont, QKeySequence
from PyQt6.QtCore import Qt, QSettings, QCoreApplication, QVariant
from PyPDF2 import PdfReader, PdfWriter

APPLICATION_NAME = "PDF Metadata Editor"
VERSION = 0.2
URL_GITHUB = "https://github.com/Manitary/PDF-Metadata-Editor"
ORGANIZATION_NAME = "Manitary"

QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
QCoreApplication.setOrganizationDomain(URL_GITHUB)
QCoreApplication.setApplicationName(APPLICATION_NAME)
settings = QSettings()
if not settings.value("LoggingLevel"):
    settings.setValue("LoggingLevel", 0)

#The tuples are sorted as they appear in the menu -- keep DEBUG last
LOGGING_LEVELS = ('NONE', 'ERROR', 'DEBUG')
LOGGING_LEVELS_TEXT = ('Disabled', 'Errors only', 'Detailed')

parser = argparse.ArgumentParser(description="copy a PDF file with altered metadata")
parser.add_argument('-d', '--debug', action='store_true', help='run with enhanced logging')

TAGS = ['/Title', '/Author', '/Subject', '/Keywords', '/Producer', '/Creator']

class MainWindow(QMainWindow):
    def __init__(self, debug=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialiseLogger()
        self.initializeUI()
        if debug:
            self.debug_toggle_act.setChecked(True)
            self.toggleLoggingLevel(-1) #Index of DEBUG option
        else:
            self.toggleLoggingLevel(settings.value("LoggingLevel"))
    
    def initialiseLogger(self):
        logFileName = f"logs/{datetime.now().strftime('%Y%m%d%H%M%S%f')}.log"
        os.makedirs(os.path.dirname(logFileName), exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.FileHandler(logFileName, delay=True))

    def initializeUI(self):
        self.path = os.path.expanduser('~')
        self.setGeometry(400, 400, 500, 100)
        self.setWindowTitle(APPLICATION_NAME)
        self.createActions()
        self.createMenu()
        self.centralWidget = QWidget()
        self.setAcceptDrops(True)
        self.setCentralWidget(self.centralWidget)
        self.form = QFormLayout(self.centralWidget)
        self.form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.file_name = str(url.toLocalFile())
            if self.file_name.endswith('.pdf'):
                self.openFile()
                break

    def createActions(self):
        self.quit_act = QAction("Quit")
        self.quit_act.triggered.connect(self.close)
        self.open_act = QAction("Open")
        self.open_act.setShortcut(QKeySequence.StandardKey.Open)
        self.open_act.triggered.connect(self.selectFile)
        self.about_act = QAction("About")
        self.about_act.triggered.connect(self.showAbout)

    def createMenu(self):
        self.menuBar().setNativeMenuBar(False)
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.open_act)
        file_menu.addAction(self.quit_act)
        help_menu = self.menuBar().addMenu("Help")
        logging_menu = QMenu("Logging", self)
        logging_options = QActionGroup(logging_menu)
        for i, level in enumerate(LOGGING_LEVELS):
            action = QAction(LOGGING_LEVELS_TEXT[i], logging_menu, checkable=True, checked=i==int(settings.value("LoggingLevel")))
            action.setData(QVariant(i))
            if level == 'DEBUG':
                self.debug_toggle_act = action
            logging_menu.addAction(action)
            logging_options.addAction(action)
        logging_options.triggered.connect(self.toggleLoggingLevelManual)
        help_menu.addMenu(logging_menu)
        help_menu.addAction(self.about_act)
    
    def toggleLoggingLevelManual(self, action):
        self.toggleLoggingLevel(action.data())
        settings.setValue("LoggingLevel", action.data())

    def toggleLoggingLevel(self, value):
        match value:
            case 0:
                self.logger.setLevel(100)
            case x:
                self.logger.setLevel(LOGGING_LEVELS[x])

    def showAbout(self):
        QMessageBox.about(self, "About",
        f'''
        <p>PDF Metadata Editor v{VERSION}</p>

        Source code available on <a href="{URL_GITHUB}">GitHub</a>
        ''')

    def selectFile(self):
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Select file", self.path, "PDF files (*.pdf)")
        if self.file_name:
            self.openFile()

    def logException(self, exception):
        self.logger.exception(f"\n[ERROR] - {datetime.now().isoformat()}")
        QMessageBox.critical(self, "Error", f"An exception of type {type(exception).__name__} occurred.<p>Arguments:\n{exception.args!r}", QMessageBox.StandardButton.Ok)

    def openFile(self):
        try:
            self.path = os.path.dirname(self.file_name)
            self.file_reader = PdfReader(self.file_name)
            self.meta = self.file_reader.metadata
        except Exception as e:
            if type(e).__name__ == "FileNotDecryptedError":
                QMessageBox.critical(self, "Error", f"The file is protected by password")
            else:
                self.logException(e)
        else:
            '''
            for i in reversed(range(self.form.count())):
                self.form.removeRow(i)
            '''
            '''
            removeRow() gives error messages when deleting some rows (maybe those with a layout?)
            So we try all possible ways of catching widgets to deleteLater(), then removeRow()
            item -> spanning -> Widget
                             -> HBoxLayout -> Widgets
                 -> else -> Label -> Widget
                         -> Field -> Widget
                                  -> HboxLayout -> Widgets
            '''
            for _ in range(self.form.rowCount()):
                if self.form.itemAt(0, QFormLayout.ItemRole.SpanningRole):
                    if self.form.itemAt(0, QFormLayout.ItemRole.SpanningRole).widget():
                        self.form.itemAt(0).widget().deleteLater()
                    else:
                        for j in range(self.form.itemAt(0, QFormLayout.ItemRole.SpanningRole).count()):
                            self.form.itemAt(0, QFormLayout.ItemRole.SpanningRole).itemAt(j).widget().deleteLater()
                else:
                    if self.form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget():
                        self.form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget().deleteLater()
                    if self.form.itemAt(0, QFormLayout.ItemRole.FieldRole).widget():
                        self.form.itemAt(0, QFormLayout.ItemRole.FieldRole).widget().deleteLater()
                    else:
                        for j in range(self.form.itemAt(0, QFormLayout.ItemRole.FieldRole).count()):
                            self.form.itemAt(0, QFormLayout.ItemRole.FieldRole).itemAt(j).widget().deleteLater()
                self.form.removeRow(0)
            self.setUpMainWindow()

    def setUpMainWindow(self):
        self.title = QLabel(Path(self.file_name).name)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Sans Serif", 14))
        self.form.addRow(self.title)
        self.form.addRow(QLabel())
        self.file_path = QLineEdit(self.file_name)
        self.file_path.setEnabled(False)
        self.form.addRow('Path', self.file_path)
        self.tag_values = []
        for tag in TAGS:
            value = self.meta.pop(tag, '')
            self.tag_values.append(value or '')
            e = QLineEdit(value)
            b = QPushButton("Reset")
            b.clicked.connect(self.resetValue)
            h = QHBoxLayout()
            h.addWidget(e)
            h.addWidget(b)
            self.form.addRow(tag[1:], h)
        for data in self.meta:
            w = QLineEdit(self.meta[data])
            w.setEnabled(False)
            self.form.addRow(data[1:], w)
        self.h_buttons = QHBoxLayout()
        self.save_button = QPushButton('Save')
        self.reset_button = QPushButton('Reset All')
        self.h_buttons.addWidget(self.save_button)
        self.h_buttons.addWidget(self.reset_button)
        self.save_button.clicked.connect(self.saveFile)
        self.reset_button.clicked.connect(self.resetValues)
        self.form.addRow(QLabel())
        self.form.addRow(self.h_buttons)
        self.centralWidget.adjustSize()

    def saveFile(self):
        new_metadata = {}
        is_changed = []
        for row in range(3, self.form.rowCount() - 2):
            #3: skip Title | Empty Line | Path
            #2: skip Empty Line | Buttons
            try:
                new_metadata[f"/{self.form.itemAt(row, QFormLayout.ItemRole.LabelRole).widget().text()}"] = self.form.itemAt(row, QFormLayout.ItemRole.FieldRole).itemAt(0).widget().text()
                is_changed.append(self.form.itemAt(row, QFormLayout.ItemRole.FieldRole).itemAt(0).widget().isModified())
            except Exception:
                new_metadata[f"/{self.form.itemAt(row, QFormLayout.ItemRole.LabelRole).widget().text()}"] = self.form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().text()
                is_changed.append(self.form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget().isModified())
        change_list = "<br>".join(TAGS[i][1:] for i in range(len(TAGS)) if is_changed[i])
        answer = QMessageBox.question(self, "Confirm changes?", f"Apply changes to the following metadata?<p>{change_list}", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            try:
                os.rename(self.file_name, f"{self.file_name}_backup")
            except Exception as e:
                if type(e).__name__ == "FileExistsError":
                    QMessageBox.critical(self, "Error", "Cannot create a backup file, when that file already exists")
                else:
                    self.logException(e)
            else:
                file_writer = PdfWriter()
                file_writer.append_pages_from_reader(self.file_reader)
                file_writer.add_metadata(new_metadata)
                try:
                    with open(self.file_name, 'wb') as f:
                        file_writer.write(f)
                except Exception as e:
                    self.logException(e)

    def resetValues(self):
        #3: skip Title | Empty Line | Path
        for tag in range(len(TAGS)):
            self.form.itemAt(3 + tag, QFormLayout.ItemRole.FieldRole).itemAt(0).widget().setText(self.tag_values[tag])
    
    def resetValue(self):
        #3: skip Title | Empty Line | Path
        for tag in range(len(TAGS)):
            if self.sender() == self.form.itemAt(3 + tag, QFormLayout.ItemRole.FieldRole).itemAt(1).widget():
                self.form.itemAt(3 + tag, QFormLayout.ItemRole.FieldRole).itemAt(0).widget().setText(self.tag_values[tag])

def main():
    app = QApplication(sys.argv)
    window = MainWindow(debug=args.debug)
    sys.exit(app.exec())

if __name__ == '__main__':
    args = parser.parse_args()
    main()