from gloome.utils import *
from shutil import rmtree


items_to_delete = []
for current_directory in (IN_DIR, OUT_DIR, LOGS_DIR, TMP_DIR):
    items_to_delete += get_items_to_delete(current_directory, FILE_RETENTION_DAYS)

items_to_delete.sort(key=lambda x: len(x.parts), reverse=True)

for current_item in items_to_delete:
    try:
        if current_item.is_file():
            print(f'delete file: {current_item}')
            current_item.unlink()
        elif current_item.is_dir():
            print(f'delete directory: {current_item}')
            rmtree(current_item)
    except Exception as e:
        print(f'Item delete error -> Current item: {current_item}',
              f'Item delete error -> Exception text: {e}',
              sep='\n')
