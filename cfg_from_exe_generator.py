import r2pipe


def create_cfgs_from_exe(exe_dist, save_path):
    # Open the binary
    r2 = r2pipe.open(exe_dist)

    # Perform initial analysis
    r2.cmd("aaa")

    # List functions
    functions = r2.cmdj("aflj")

    # function_address = functions[0]
    # r2.cmd(f"agf @ {function_address}")
    # print(functions[0]["addr"])

    # save_path = "D:\MyNauchWork\cfg"
    # Iterate through functions and generate CFGs
    for func in functions:
        function_address = func["offset"]
        r2.cmd(f"agf @ {function_address}")
        print(func)
        # Extract and save CFG information to a text document
        cfg_info = r2.cmd(f"agj {function_address}")
        with open( save_path + f"cfg_{function_address}.txt", "w") as file:
            file.write(cfg_info)
            print("Sucsessfully!")

    r2.quit()

# cflinks = r2.cmd("agCj")
# with open (save_path + "cflinks.txt", "w") as fl:
#     fl.write(cflinks)

create_cfgs_from_exe("F:\programming 2024\Sci_Research\sources\Homework2.exe", "F:\\programming 2024\\Sci_Research\\cfg2\\")

# Close Radare2
#r2.quit()


