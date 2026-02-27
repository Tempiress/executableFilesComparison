import re
import os
import click
import r2pipe
import hashlib
import shutil
import tempfile
from pathlib import Path
import asm2vec
import torch
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def sha3(data):
    return hashlib.sha3_256(data.encode()).hexdigest()


def validEXE(filename):
    # Проверка магических чисел: ELF (Linux) или MZ (Windows)
    magics = [bytes.fromhex('7f454c46'), bytes.fromhex('4d5a')]
    try:
        with open(filename, 'rb') as f:
            header = f.read(2)  # Читаем первые 2 байта (достаточно для MZ)
            # Для ELF нужно 4 байта, но проверим начало
            if header == bytes.fromhex('4d5a'): return True
            f.seek(0)
            header = f.read(4)
            return header == bytes.fromhex('7f454c46')
    except Exception:
        return False


def normalize(opcode):
    opcode = opcode.replace(' - ', ' + ')
    opcode = re.sub(r'0x[0-9a-f]+', 'CONST', opcode)
    opcode = re.sub(r'\*[0-9]', '*CONST', opcode)
    opcode = re.sub(r' [0-9]', ' CONST', opcode)
    return opcode


def fn2asm(pdf, minlen):
    # 1. Проверка на пустоту
    if pdf is None or 'ops' not in pdf:
        return None

    ops = pdf['ops']

    # 2. Фильтр по длине
    if len(ops) < minlen:
        return None

    # 3. Фильтр невалидных инструкций
    if 'invalid' in [op.get('type', '') for op in ops]:
        return None

    # 4. Нормализация адресов и сбор меток
    labels = {}
    scope = set()

    # Сначала собираем все адреса инструкций в этом блоке
    for op in ops:
        addr = op.get('offset', op.get('addr'))
        if addr is not None:
            scope.add(addr)
            op['addr'] = addr  # Унифицируем ключ

    # Теперь ищем переходы ВНУТРИ функции
    for i, op in enumerate(ops):
        target = op.get('jump')
        if target is not None and target in scope:
            labels.setdefault(target, i)

    # 5. Генерация текста
    output = ''
    for op in ops:
        cur_addr = op['addr']

        # Добавляем метку (LABEL:), если на этот адрес есть переход
        if cur_addr in labels:
            output += f'LABEL{labels[cur_addr]}:\n'

        # Формируем инструкцию
        # ВАЖНО: Используем мнемонику (je, call), а не тип (cjmp, ucall)
        # r2 кладет мнемонику в 'opcode' (например "je 0x401000") или 'disasm'
        full_opcode = op.get('opcode') or op.get('disasm', '')
        mnemonic = full_opcode.split()[0] if full_opcode else op.get('type', 'nop')

        target = op.get('jump')
        if target is not None and target in labels:
            # Инструкция с переходом на метку (внутри функции)
            output += f' {mnemonic} LABEL{labels[target]}\n'
        else:
            # Обычная инструкция
            output += f' {normalize(full_opcode)}\n'

    return output


def bin2asm(filename, opath, minlen):
    # Если это не валидный бинарник, пробуем продолжить (вдруг это shellcode), но с логом
    if not validEXE(filename):
        logging.info(f"File {filename} header not recognized, trying anyway...")

    try:
        # Открываем r2. flags=['-2'] отключает stderr для чистоты
        r = r2pipe.open(str(filename), flags=["-2"])
        r.cmd('aaaa')  # Анализ
    except Exception as e:
        logging.error(f"Failed to open {filename}: {e}")
        return 0

    count = 0
    # Получаем список всех функций
    functions = r.cmdj('aflj')

    if not functions:
        logging.warning(f"No functions found in {filename}")
        r.quit()
        return 0

    for fn in functions:
        func_addr = fn['addr']
        func_size = fn.get('size', 0)
        func_name = fn.get('name', f"func_{func_addr:x}")

        # Санитизация имени
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', func_name)
        if not safe_name:
            safe_name = f"{func_addr:x}"

        # 1. Пробуем умный дизассемблинг (граф)
        ops_json = r.cmdj(f'pdfj @ {func_addr}')

        # 2. Fallback: если граф не построился, берем линейный дамп
        if not ops_json or not ops_json.get('ops'):
            if func_size > 0:
                try:
                    raw_ops = r.cmdj(f'pDj {func_size} @ {func_addr}')
                    if raw_ops:
                        ops_json = {'ops': raw_ops, 'name': func_name}
                except Exception:
                    pass

        # Если все равно пусто — пропускаем
        if not ops_json:
            continue

        asm = fn2asm(ops_json, minlen)

        if asm:
            uid = safe_name
            # Заголовок с точкой и пробелом, чтобы Function.load понял, что это метаданные
            header = f' .name {func_name}\n .offset {func_addr:016x}\n .file {filename.name}\n'
            full_asm = header + asm

            try:
                # Создаем файл
                out_file = opath / uid
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(full_asm)
                count += 1
            except Exception as e:
                logging.error(f"Error writing file {uid}: {e}")

    r.quit()
    return count


def cosine_similarity(v1, v2):
    return (v1 @ v2 / (v1.norm() * v2.norm())).item()


def cli2(ipath1, ipath2, mpath, epochs, lr=0.02, device='auto'):
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Создаем временную директорию, которая удалится после выхода из блока with
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Функция для подготовки пути (если exe -> конвертируем, если папка/txt -> оставляем)
        def prepare_input(input_path):
            path_obj = Path(input_path)

            # Если это директория - возвращаем как есть
            if path_obj.is_dir():
                return path_obj

            # Если это файл, проверяем, ASM это или бинарник
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    head = f.read(10)
                    if head.strip().startswith('.name'):
                        return path_obj  # Это уже ASM
            except (UnicodeDecodeError, OSError):
                pass  # Это бинарник

            # Это бинарник, конвертируем
            print(f"[Info] Converting {path_obj.name} to ASM...")
            out_subdir = temp_path / path_obj.name
            out_subdir.mkdir(exist_ok=True)

            cnt = bin2asm(path_obj, out_subdir, minlen=10)
            if cnt == 0:
                print(f"[Warning] No functions extracted from {path_obj.name}")

            return out_subdir

        # Подготавливаем пути (конвертируем бинарники на лету)
        real_path1 = prepare_input(ipath1)
        real_path2 = prepare_input(ipath2)

        # load model, tokens
        #print("[Info] Loading model and data...")
        model, tokens = asm2vec.utils.load_model(mpath, device=device)

        # Загружаем функции из подготовленных путей
        functions, tokens_new = asm2vec.utils.load_data([real_path1, real_path2])

        if not functions:
            print("[Error] No valid functions loaded! Check binary analysis.")
            return 0.0

        #print(f"[Info] Loaded {len(functions)} functions total.")

        tokens.update(tokens_new)
        model.update(2, tokens.size())
        model = model.to(device)

        # train function embedding
        #print("[Info] Starting training/inference...")
        model = asm2vec.utils.train(
            functions,
            tokens,
            model=model,
            epochs=epochs,
            device=device,
            mode='test',
            learning_rate=lr
        )

        # Сравнение
        # В режиме test мы дообучаем вектора для НОВЫХ функций.
        # model.embeddings_f содержит вектора для functions в том порядке, в каком они в load_data
        # Если load_data загрузил [funcA_bin1, funcB_bin1, funcA_bin2, ...], то нам нужно знать, что сравнивать.
        # Для простого случая (сравнение двух файлов целиком) часто берут среднее или best match.
        # В вашем оригинальном коде брались индексы 0 и 1. Это сработает, только если в каждом бинарнике всего по 1 функции.

        # Чтобы не ломать логику, оставим как было, но добавим предупреждение
        if len(functions) < 2:
            print("[Error] Not enough functions to compare.")
            return 0.0

        v1, v2 = model.to('cpu').embeddings_f(torch.tensor([0, 1]))

        sim = cosine_similarity(v1, v2)
        # print(f'cosine similarity : {sim:.6f}')
        return round(sim, 6)


#@click.command()
#@click.option('-i', '--input', 'ipath', help='input directory / file', required=True)
#@click.option('-o', '--output', 'opath', default='asm', help='output directory')
#@click.option('-l', '--len', 'minlen', default=10,
#              help='ignore assembly code with instructions amount smaller than minlen')
def cli(ipath, opath, minlen):
    '''
    Extract assembly functions from binary executable
    '''
    ipath = Path(ipath)
    opath = Path(opath)

    # create output directory
    if not os.path.exists(opath):
        os.mkdir(opath)

    fcount, bcount = 0, 0

    # directory
    if os.path.isdir(ipath):
        for f in os.listdir(ipath):
            if not os.path.islink(ipath / f) and not os.path.isdir(ipath / f):
                fcount += bin2asm(ipath / f, opath, minlen)
                bcount += 1
    # file
    elif os.path.exists(ipath):
        fcount += bin2asm(ipath, opath, minlen)
        bcount += 1
    else:
        print(f'[Error] No such file or directory: {ipath}')

    print(f'[+] Total scan binary: {bcount} => Total generated assembly functions: {fcount}')
    return bcount, fcount


if __name__ == '__main__':
    # Пример вызова для теста (закомментировано)
    # cli("path/to/exe", "./asm", 10)
    pass