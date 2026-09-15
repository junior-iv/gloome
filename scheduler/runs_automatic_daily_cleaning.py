from gloome.utils import *
from shutil import rmtree


items_to_delete = []
for current_directory in (IN_DIR, OUT_DIR, LOGS_DIR, TMP_DIR):
    items_to_delete += get_items_to_delete(current_directory, FILE_RETENTION_DAYS)

items_to_delete.sort(key=lambda x: len(x.parts), reverse=True)

for current_item in items_to_delete:
    if current_item.is_file():
        current_item.unlink()
    elif current_item.is_dir():
        rmtree(current_item)