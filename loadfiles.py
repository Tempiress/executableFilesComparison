import os
import chardet
import magic

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_files_to_memory(folder):
    # mime = magic.Magic(mime=True)
    magic.from_file("./coreutils-polybench-hashcat/aoc/Os/ct.txt")
    files_content = {}
    file_encoding = detect_encoding(folder)
    for file_name in os.listdir(folder):
        # if file_name.endswith('.txt'):
        with open(os.path.join(folder, file_name), 'r', encoding=file_encoding) as f:
            files_content[file_name] = f.read()
    return files_content

# Использование:
# folder1_files = load_files_to_memory(folder1)
# folder2_files = load_files_to_memory(folder2)
