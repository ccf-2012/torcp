import os
import json


class CacheManager:
    def __init__(self, logdir):
        self.search_history_file_path = os.path.join(logdir, 'CACHE_LIST.json')

    def openCache(self):
        try:
            with open(self.search_history_file_path, 'r',
                      encoding='utf8') as f:
                self.search_history = json.load(f)
            self.history_json_fd = open(self.search_history_file_path,
                                        'r+',
                                        encoding='utf8')
            return True
        except:
            self.search_history = {'path_dupped': [], 'basename': []}
            self.history_json_fd = open(self.search_history_file_path,
                                        'w',
                                        encoding='utf8')
            json.dump(self.search_history, self.history_json_fd, indent=4)
            # self.history_json_fd.close()
            return False

    def isCached(self, file_path):
        for name in self.search_history['path_dupped']:
            if file_path == name:
                return True
        return False

    def append(self, file_path):
        # append file_path to history
        if file_path not in self.search_history['path_dupped']:
            self.search_history['path_dupped'].append(file_path)

        json.dump(self.search_history, self.history_json_fd, indent=4)
        self.history_json_fd.seek(0)

    def closeCache(self):
        self.history_json_fd.close()

