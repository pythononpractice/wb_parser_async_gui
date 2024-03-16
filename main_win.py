import asyncio
import datetime
from PyQt5.QtCore import pyqtSlot, QThreadPool, QRunnable
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QStyledItemDelegate, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView, \
    QTabWidget, QFormLayout, QLabel, QLineEdit, QFileDialog, QHBoxLayout, \
    QHeaderView, QTextEdit
from manager import CRUDManager
from parser import parser
from task_dialog import TaskDialog


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return


class Worker(QRunnable):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        try:
            asyncio.run(self.function(*self.args, **self.kwargs))
        except Exception as e:
            print(e)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.crud_tasks = CRUDManager('tasks.json', [])
        self.crud_config = CRUDManager('config.json', {'default_folder': ""})
        self.tasks = self.crud_tasks.read()
        self.set_appear()
        self.init_ui()
        self.connections()
        self.update_task_table()
        self.show()

    def init_ui(self):
        self.thread_pool = QThreadPool()
        # Создание виджета вкладок
        self.main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Создание вкладки "Задачи"
        self.tasks_tab = QWidget()
        self.tasks_layout = QVBoxLayout()
        self.tasks_tab.setLayout(self.tasks_layout)

        # Создание таблицы "Список задач" на вкладке "Задачи"
        self.task_table = QTableWidget()

        delegate = ReadOnlyDelegate(self.task_table)
        [self.task_table.setItemDelegateForColumn(i, delegate) for i in range(7)]

        self.task_table.setColumnCount(7)
        self.task_table.verticalHeader().setDefaultSectionSize(50)
        self.task_table.setHorizontalHeaderLabels(
            [
             'id',
             "Название",
             "Ссылка",
             "Мин. цена",
             "Макс. цена",
             "Мин. скидка",
             "Последнее обновление"
            ]
        )
        self.task_table.setColumnWidth(0, 20)
        self.task_table.setColumnWidth(1, 210)
        self.task_table.setColumnWidth(2, 220)
        self.task_table.setColumnWidth(3, 110)
        self.task_table.setColumnWidth(4, 110)
        self.task_table.setColumnWidth(5, 110)
        self.task_table.setColumnWidth(6, 190)
        self.task_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.del_btn_style = """
        QPushButton {
            background-color: #f80000;
            color: #ffffff;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }"""
        self.start_btn_style = """
        QPushButton {
            background-color: #138808;
            color: #ffffff;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }"""
        self.table_style = """
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #d9d9d9;
        }

        QTableWidget::item {
            padding: 5px;
            border: 1px solid #d9d9d9;
            background-color: #f3f3f3;
        }

        QPushButton {
            background-color: #007acc;
            color: #ffffff;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }

        QPushButton:hover {
            background-color: #005ea8;
        }
        QTableWidget::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        """

        # Установка стилей для таблицы и кнопки
        self.task_table.setStyleSheet(self.table_style)
        self.task_table.setSortingEnabled(True)

        self.tasks_layout.addWidget(self.task_table)
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.moveCursor(QTextCursor.End)
        self.tasks_layout.addWidget(self.log_text_edit)

        # Создание кнопки "Добавить новую задачу"
        self.del_task_button = QPushButton("Удалить задачу")
        self.del_task_button.setStyleSheet(self.del_btn_style)

        self.add_task_button = QPushButton("Добавить новую задачу")
        self.add_task_button.setStyleSheet(self.table_style)

        self.start_task_button = QPushButton("Запустить задачу")
        self.start_task_button.setStyleSheet(self.start_btn_style)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.start_task_button)
        self.buttons_layout.addWidget(self.add_task_button)
        self.buttons_layout.addWidget(self.del_task_button)
        self.tasks_layout.addLayout(self.buttons_layout)

        # Добавление вкладки "Задачи" в виджет вкладок
        self.tab_widget.addTab(self.tasks_tab, "Задачи")

        # Создание вкладки "Настройки"
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Добавление настроек
        # Поле для выбора папки по умолчанию
        folder_label = QLabel("Папка по умолчанию:")
        self.default_folder_input = QLineEdit(self.crud_config.get_by_key('default_folder'))
        self.folder_button = QPushButton("Выбрать папку")

        form_layout.addRow(folder_label, self.default_folder_input)
        form_layout.addRow(self.folder_button)


        # settings_layout.addWidget(self.auto_start_checkbox_default)
        settings_layout.addLayout(form_layout)

        settings_tab.setLayout(settings_layout)
        self.tab_widget.addTab(settings_tab, "Настройки")

        self.main_layout.addWidget(self.tab_widget)
        self.setLayout(self.main_layout)

    def set_appear(self):
        self.setWindowTitle("Парсер Wildberries")
        self.resize(1200, 600)

    def connections(self):
        self.add_task_button.clicked.connect(self.create_task)
        self.del_task_button.clicked.connect(self.delete_task)
        self.start_task_button.clicked.connect(self.start_task)
        self.folder_button.clicked.connect(self.choose_default_folder)
        self.task_table.itemDoubleClicked.connect(self.edit_task)

    def create_task(self):
        dialog = TaskDialog({
            "name": '',
            "link": '',
            "low_price": '',
            "top_price": '',
            "discount": 0,
        })
        if dialog.exec_():
            # Получаем данные из диалогового окна
            task_data = dialog.get_task_data()
            # Добавляем новую задачу в список задач
            task_data['id'] = self.tasks[-1]['id'] + 1 if len(self.tasks) > 0 else 1
            self.tasks.append(task_data)
            # Обновляем JSON файл с задачами
            self.crud_tasks.update(self.tasks)
            # Обновляем таблицу задач
            self.update_task_table()

    def edit_task(self, item):
        row = item.row()
        # Получаем id задачи, на которую был сделан двойной клик
        task_id = int(self.task_table.item(row, 0).text())
        current_task = next((task for task in self.tasks if task["id"] == task_id), None)
        if current_task:
            dialog = TaskDialog(current_task)
            if dialog.exec_():
                # Обновляем данные задачи после редактирования
                updated_task = dialog.get_task_data()
                index = self.tasks.index(current_task)
                self.tasks[index] = updated_task
                self.crud_tasks.update(self.tasks)
                self.update_task_table()

    def delete_task(self):
        selected_item = self.task_table.selectedItems()
        if len(selected_item) > 0:
            task_id = self.task_table.item(selected_item[0].row(), 0).text()
            current_task = list(filter(lambda t: t['id'] == int(task_id), self.tasks))[0]
            self.tasks.remove(current_task)
            self.crud_tasks.update(self.tasks)
            self.update_task_table()

    def choose_default_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder:
            try:
                self.default_folder_input.setText(folder)
                self.crud_config.update_by_key('default_folder', folder)
            except Exception as e:
                print(e)

    def update_task_table(self):
        self.task_table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            self.task_table.setItem(row, 0, QTableWidgetItem(str(task["id"])))
            self.task_table.setItem(row, 1, QTableWidgetItem(task["name"]))
            self.task_table.setItem(row, 2, QTableWidgetItem(task["link"]))
            self.task_table.setItem(row, 3, QTableWidgetItem(str(task["low_price"])))
            self.task_table.setItem(row, 4, QTableWidgetItem(str(task["top_price"])))
            self.task_table.setItem(row, 5, QTableWidgetItem(str(task["discount"])))
            self.task_table.setItem(row, 6, QTableWidgetItem(task["last_update"]))

    def start_task(self):
        selected_item = self.task_table.selectedItems()
        if len(selected_item) > 0:
            task_id = self.task_table.item(selected_item[0].row(), 0).text()
            current_task = list(filter(lambda t: t['id'] == int(task_id), self.tasks))[0]
            self.log_text_edit.append(f"Задача {current_task['name']} запущена!")
            try:
                worker = Worker(
                    parser,
                    log_output=self.log_text_edit,
                    url=current_task['link'],
                    low_price=int(current_task['low_price']),
                    top_price=int(current_task['top_price']),
                    discount=int(current_task['discount']),
                    save_path=self.default_folder_input.text()
                )
                self.thread_pool.start(worker)
                current_task['last_update'] = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
            except:
                self.log_text_edit.append(f"Произошла ошибка, проверьте правильность ввода данных.")

            # parser(url=current_task['link'], low_price=current_task['low_price'], top_price=current_task['top_price'], discount=current_task['discount'])
