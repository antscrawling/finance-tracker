from PyQt5.QtWidgets import QMessageBox, QFileDialog

def export_to_csv(self):
    try:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Transactions",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Type", "Category", "Amount", "Balance"])
                
                for row in range(self.transactions_table.rowCount()):
                    row_data = []
                    for col in range(self.transactions_table.columnCount()):
                        row_data.append(self.transactions_table.item(row, col).text())
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Success", "Transactions exported successfully!")
    
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")