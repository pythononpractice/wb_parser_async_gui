import datetime

from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QFormLayout


class TaskDialog(QDialog):
    def __init__(self, task_data):
        super().__init__()
        self.task_data = task_data
        self.setWindowTitle("Редактировать задачу")
        self.init_ui()

    def init_ui(self):

        self.task_name_input = QLineEdit(self.task_data["name"])
        self.link_input = QLineEdit(self.task_data["link"])
        self.low_price_input = QLineEdit(str(self.task_data["low_price"]))
        self.top_price_input = QLineEdit(str(self.task_data["top_price"]))
        self.discount_input = QLineEdit(str(self.task_data["discount"]))

        save_button = QPushButton("Сохранить")

        # Создание макета для полей в диалоговом окне
        form_layout = QFormLayout()
        form_layout.addRow("Название задачи:", self.task_name_input)
        form_layout.addRow("Ссылка:", self.link_input)
        form_layout.addRow("Мин. цена:", self.low_price_input)
        form_layout.addRow("Макс. цена:", self.top_price_input)
        form_layout.addRow("Мин. скидка:", self.discount_input)
        form_layout.addRow(save_button)
        self.setLayout(form_layout)
        save_button.clicked.connect(self.save_changes)


    def save_changes(self):
        # Сохраняем введенные данные в словарь задачи
        try:
            self.task_data["name"] = self.task_name_input.text()
            self.task_data["link"] = self.link_input.text()
            self.task_data["low_price"] = int(self.low_price_input.text())
            self.task_data["top_price"] = int(self.top_price_input.text())
            self.task_data["discount"] = int(self.discount_input.text())
            if not 'last_update' in self.task_data:
                self.task_data["last_update"] = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
            self.accept()
        except Exception as e:
            print(e)

    def get_task_data(self):
        # Возвращаем обновленные данные задачи
        return self.task_data