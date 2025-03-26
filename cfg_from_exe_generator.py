import r2pipe
import os
import logging


def create_cfgs_from_exe(exe_dist, save_path):
    """
    Извлекает CFG из исполняемого файла с помощью Radare2.
    :param exe_dist: Путь к исполняемому файлу.
    :param save_path: Директория для сохранения CFG.
    """

    # Open the binary
    try:
        r2 = r2pipe.open(exe_dist, flags=["-2"])

        # Perform initial analysis
        r2.cmd("aaa")
        # List functions
        functions = r2.cmdj("aflj")
        if not functions:
            raise ValueError("No functions found in the binary.")
    except Exception as e:
        logging.error(f"Error processing file {exe_dist}: {e}")

    # function_address = functions[0]
    # r2.cmd(f"agf @ {function_address}")
    # print(functions[0]["addr"])

    if not os.path.exists(".\\cfg1"): os.mkdir(".\\cfg1")
    if not os.path.exists(".\\cfg2"): os.mkdir(".\\cfg2")

    # Iterate through functions and generate CFGs
    for func in functions:
        function_address = func["offset"]
        name = func["name"]
        r2.cmd(f"agf @ {function_address}")

        # Extract and save CFG information to a text document
        cfg_info = r2.cmd(f"agj {function_address}")
        # with open(save_path + f"cfg_{function_address}.txt", "w") as file:
        with open(save_path + f"{name}.txt", "w") as file:
            file.write(cfg_info)

    r2.quit()


def call_func_graph(exe_dist, save_name):
    """
    Создание файла связей блоков (Imports)
    :param exe_dist:
    :param save_name:
    :return: file
    """
    r2 = r2pipe.open(exe_dist, flags=["-2"])
    r2.cmd("aaa")
    cflinks = r2.cmd("agCj")
    with open(save_name, "w") as fl:
        fl.write(cflinks)
    r2.quit()

# call_func_graph(".\\HW3.exe", ".\\cfgcflinks2")
# create_cfgs_from_exe(".\\sources\\Homework2.exe", ".\\cfg2\\")
# Close Radare2
# r2.quit()





