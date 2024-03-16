import json
import os


class CRUDManager():
    def __init__(self, file_path, init_data):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            file_data = init_data
            with open(self.file_path, 'w') as file:
                json.dump(file_data, file, indent=4)

    def read(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            return []

    def update(self, new_data):
        data = new_data
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)
        return True

    def update_by_key(self, key, new_data):
        data = self.read()
        data[key] = new_data
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)
        return True

    def get_by_key(self, key):
        data = self.read()
        return data[key]
