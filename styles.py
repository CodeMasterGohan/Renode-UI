"""
Styles Module.

This module defines the QSS (Qt Style Sheet) constants used to theme the application.
It provides a Dark Theme implementation for various Qt widgets.
"""

DARK_THEME_QSS = """
/* Global Styles */
QMainWindow, QWidget {
    background-color: #202020;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 10pt;
}

/* Push Buttons */
QPushButton {
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #444444;
    border-color: #555555;
}

QPushButton:pressed {
    background-color: #2a2a2a;
    border-color: #444444;
}

QPushButton:disabled {
    background-color: #252525;
    color: #666666;
    border-color: #333333;
}

/* Input Fields */
QLineEdit, QTextEdit {
    background-color: #2d2d2d;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0078d4;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3e3e3e;
    background-color: #202020;
    top: -1px; 
}

QTabBar::tab {
    background-color: #2d2d2d;
    border: 1px solid #3e3e3e;
    padding: 6px 12px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    color: #cccccc;
}

QTabBar::tab:selected {
    background-color: #202020;
    border-bottom-color: #202020; /* Blend with pane */
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #383838;
}

/* Table Widget */
QTableWidget {
    background-color: #2d2d2d;
    border: 1px solid #3e3e3e;
    gridline-color: #3e3e3e;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #333333;
    color: #e0e0e0;
    padding: 4px;
    border: 1px solid #3e3e3e;
}

QTableCornerButton::section {
    background-color: #333333;
    border: 1px solid #3e3e3e;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: none;
    background: #2d2d2d;
    width: 12px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #444444;
    min-height: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #2d2d2d;
    height: 12px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:horizontal {
    background: #444444;
    min-width: 20px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: #555555;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

/* Dialogs */
QDialog {
    background-color: #202020;
}

QLabel {
    color: #e0e0e0;
}

QComboBox {
    background-color: #333333;
    border: 1px solid #444444;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #444444;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
"""
