import re

ASM_FILE = "./ASM.txt"
BIN_FILE = "./BIN.txt"

R = {
    "R0": "00",
    "R1": "01",
    "R2": "10",
    "R3": "11",
}

line_dict = {}
instructions = {}
comments = {}
labels = {}
to_bin = []

def line_separator(line: str):
    # retorna mne, endereço e comentário
    aux: list[str] = []
    instr: str = None
    comment: str = None
    label: str = None

    if "#" in line:
        aux = re.split(" # ", line)
        
        instr = aux[0] if (len(aux) > 1 and ":" not in line) else None

        comment = aux[1].replace("\n", "") if len(aux) > 1 else aux[0].replace("\n", "")

        label = aux[0].split(":")[0] if ":" in line else None
    else:
        instr = None if ":" in line else line.replace("\n", "")
        label = line.split(":")[0] if ":" in line else None

    return instr, comment, label

def instruction_separator(instr: str):
    aux: list[str] = []
    mnemonic: str = None
    arg1: str = None
    arg2: str = None

    if instr is not None:
        aux = instr.split(" ")

        mnemonic = aux[0]

        if len(aux) == 2:
            arg1 = aux[1]
        
        if len(aux) == 3:
            arg1 = aux[1]
            arg2 = aux[2]

    return {"mnemonic": mnemonic, "arg1": arg1, "arg2": arg2}

def tmp_format(index: int, mnemonic: str, arg1: str, arg2: str, comment: str):
    reg_value: str = "R0"
    immed_value: str = bin(0)[2:].zfill(9)
    instr_comm: str = f"-- {mnemonic} "

    if arg1 is not None and arg1.startswith("$"):
        reg_value = arg1.split("$")[1]

        if arg2 is not None:
            immed_value = arg2.split("@")[1] if arg2.startswith("@") else arg2.split("$")[1]
            
            instr_comm += f"{arg1} {arg2} {comment}"

        return f"tmp({index}) := {mnemonic} & \"{R[reg_value]}\" & \"{bin(int(immed_value))[2:].zfill(9)}\";\t{instr_comm}\n"

    if arg1 is not None:
        immed_value = arg1.split("@")[1]

        instr_comm += f"{arg1} {comment}"

        try:
            return f"tmp({index}) := {mnemonic} & \"{R[reg_value]}\" & \"{bin(int(immed_value))[2:].zfill(9)}\";\t{instr_comm}\n"
        except:
            raise ValueError(f"Erro de sintaxe na linha {index}. Verifique e tente novamente.")

    else:
        instr_comm += f"{comment}"

        return f"tmp({index}) := {mnemonic} & \"{R[reg_value]}\" & \"{bin(int(immed_value))[2:].zfill(9)}\";\t{instr_comm}\n"

def main():
    label_cont = 0
    line_index = 0
    tmp_index = 0
    comm_cont = 0
    comm_index = 0

    with open(ASM_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(BIN_FILE, "w+", encoding="utf-8") as file:
        for line in lines:
            if not line.startswith("\n"):
                instr, comment, label = line_separator(line)

                separated_instr: dict[str, str] = instruction_separator(instr)

                if label is not None:
                    labels[line_index - label_cont] = label
                    label_cont += 1

                if comment is not None and separated_instr["mnemonic"] is not None:
                    comments[line_index] = comment

                line_dict[line_index] = {"instr": separated_instr, "comment": comment, "label": label}

                line_index += 1

        for k, v in line_dict.items():
            for kl, label in labels.items():
                if v["instr"]["arg1"] is not None and label in v["instr"]["arg1"]:
                    aux = v["instr"]["arg1"].split("@")
                    aux[1] = str(kl)
                    v["instr"]["arg1"] = "@".join(aux)

        for k, v in line_dict.items():
            if v["instr"]["mnemonic"] not in [None, ""]:
                new_line = tmp_format(tmp_index, v["instr"]["mnemonic"], v["instr"]["arg1"], v["instr"]["arg2"], "")

                try:
                    file.write(new_line)
                except TypeError:
                    print(new_line)
                    break

                tmp_index += 1

if __name__ == "__main__":
    main()