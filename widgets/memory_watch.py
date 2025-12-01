"""
Memory Watch Widget Module.

This module provides the UI components for watching memory addresses in the Renode simulation.
It includes a dialog for adding new watches and a main widget for displaying and managing
the list of watched addresses.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt

class AddWatchDialog(QDialog):
    """
    A dialog for adding a new memory watch.

    Allows the user to input the memory address (in hex), a descriptive name,
    and the data type (Word, Byte, HalfWord).
    """

    def __init__(self, parent=None):
        """
        Initializes the AddWatchDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Add Memory Watch")
        
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.address_input = QLineEdit()
        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["Word", "Byte", "HalfWord"])
        
        self.form_layout.addRow("Address (Hex):", self.address_input)
        self.form_layout.addRow("Name:", self.name_input)
        self.form_layout.addRow("Type:", self.type_input)
        
        self.layout.addLayout(self.form_layout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        """
        Retrieves the data entered by the user.

        Returns:
            dict: A dictionary containing 'address', 'name', and 'type'.
        """
        return {
            "address": self.address_input.text(),
            "name": self.name_input.text(),
            "type": self.type_input.currentText()
        }

class MemoryWatchWidget(QWidget):
    """
    A widget for displaying and managing memory watches.

    Provides a table view of watched memory addresses and buttons to add or remove watches.
    """

    def __init__(self):
        """
        Initializes the MemoryWatchWidget.
        """
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Address", "Name", "Type", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Watch")
        self.add_btn.clicked.connect(self.add_watch)
        self.remove_btn = QPushButton("Remove Watch")
        self.remove_btn.clicked.connect(self.remove_watch)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        self.layout.addLayout(btn_layout)
        
        self.watches = [] # List of dicts: {address, name, type, row_index}

    def add_watch(self):
        """
        Opens the AddWatchDialog and adds a new watch if confirmed.

        Validates that the address is a valid hex string before adding.
        """
        dialog = AddWatchDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                addr_int = int(data["address"], 16)
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                self.table.setItem(row, 0, QTableWidgetItem(hex(addr_int)))
                self.table.setItem(row, 1, QTableWidgetItem(data["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(data["type"]))
                self.table.setItem(row, 3, QTableWidgetItem("N/A"))
                
                self.watches.append({
                    "address": addr_int,
                    "name": data["name"],
                    "type": data["type"],
                    "row": row
                })
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Address must be a valid hex string (e.g., 0x1000)")

    def remove_watch(self):
        """
        Removes the currently selected watch from the table and internal list.
        """
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            # Remove from self.watches list - need to handle index shifting or rebuild list
            # For simplicity, we'll just rebuild the list from the table or handle it carefully
            # Actually, simpler to just remove by index if we track it, but row indices change.
            # Let's just remove the item that matches the row.
            # A better way for production is to store data in the item or use a model.
            # For this MVP, let's just pop it if we can find it, or better:
            # Rebuild self.watches from table content is safest for simple logic
            self.rebuild_watches()

    def rebuild_watches(self):
        """
        Rebuilds the internal list of watches from the table contents.

        This ensures the internal state matches the UI state after row removal.
        """
        self.watches = []
        for row in range(self.table.rowCount()):
            addr_str = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            type_ = self.table.item(row, 2).text()
            self.watches.append({
                "address": int(addr_str, 16),
                "name": name,
                "type": type_,
                "row": row
            })

    def update_value(self, row, value):
        """
        Updates the displayed value for a specific row in the watch table.

        Args:
            row (int): The row index to update.
            value (int): The new value to display (will be formatted as hex).
        """
        self.table.setItem(row, 3, QTableWidgetItem(hex(value)))
