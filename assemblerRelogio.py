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
comments = []
labels = {}
to_bin = []

def line_separator(line: str) -> list[str]:
    '''
    Recebe uma linha (`str`) de um arquivo ASM.txt e armazena o conteúdo em uma lista. 
    
    Parameters
    ----------
    line (`str`): a linha do arquivo ASM.txt

    Returns
    ----------
    `list[str]`: uma lista contendo instrução, comentário e *label*

    Examples
    ----------
    >>> line_separator("STA $R1 @256 # comentário genérico")
    ["STA $R1 @256", "comentário genérico", None]

    >>> line_separator("main: # comentário genérico")
    [None, "comentário genérico", "main"]

    >>> line_separator("# comentário genérico")
    [None, "comentário genérico", None]
    '''
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

    return [instr, comment, label]

def instruction_separator(instr: str) -> dict[str, str | None]:
    '''
    Recebe uma instrução e separa o mnemônico de seus argumentos (se tiver).

    Parameters
    ----------
    instr (`str`): instrução a ser separada

    Returns
    ----------
    `dict[str, str]`: um dicionário no formato `{"mnemonic": mnemonic, "arg1": arg1, "arg2": arg2}`

    Examples
    ----------
    >>> instruction_separator("STA $R1 @256")
    {"mnemonic": "STA", "arg1": "$R1", "arg2": "@256"}

    >>> instruction_separator("JMP @label_generica")
    {"mnemonic": "JMP", "arg1": "@label_generica, "arg2": None}

    >>> instruction_separator("RET")
    {"mnemonic": "RET", "arg1": None, "arg2": None}
    '''
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

def tmp_format(index: int, mnemonic: str, arg1: str, arg2: str, comment: str) -> str:
    '''
    Formata uma instrução para uma *string* "tmp", que pode ser passada para o arquivo memoriaROM.vhdl
    
    Parameters
    ----------
    index (`int`): índice da instrução
    mnemonic (`str`): mnemônico
    arg1 (`str`): argumento 1 da instrução
    arg2 (`str`): argumento 2 da instrução
    comment (`str`): comentário da linha de índice *index*

    Returns
    ----------
    Uma string no formato tmp(index) := MNE & REG $ IMMED\t;-- comentário

    Examples
    ----------

    >>> tmp_format(1, "STA", "$R1", "@256", "comentário genérico")
    tmp(1) = STA & "01" & "100000000"";\t-- STA $R1 @256 # comentário genérico

    >>> tmp_format(2, "RET", None, None, "")
    tmp(1) = RET & "0o" & "000000000"";\t-- RET
    '''
    reg_value: str = "R0"
    immed_value: str = bin(0)[2:].zfill(9)
    instr_comm: str = f"-- {mnemonic} "
    asm_comment: str = ""

    if comment is not None:
        asm_comment = f"# {comment}"

    if arg1 not in [None, ""] and arg1.startswith("$"):
        reg_value = arg1.split("$")[1]

        if arg2 is not None:
            immed_value = arg2.split("@")[1] if arg2.startswith("@") else arg2.split("$")[1]
            
            instr_comm += f"{arg1} {arg2} {asm_comment}"

        return f"tmp({index}) := {mnemonic} & \"{R[reg_value]}\" & \"{bin(int(immed_value))[2:].zfill(9)}\";\t{instr_comm}\n"

    if arg1 not in [None, ""]:
        immed_value = arg1.split("@")[1]

        instr_comm += f"{arg1} {asm_comment}"

        try:
            return f"tmp({index}) := {mnemonic} & \"{R[reg_value]}\" & \"{bin(int(immed_value))[2:].zfill(9)}\";\t{instr_comm}\n"
        except:
            raise ValueError(f"Erro de sintaxe na linha {index}. Verifique e tente novamente.")

    else:
        instr_comm += f"# {comment}"

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
                    comments.append(comment)

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
                new_line = tmp_format(tmp_index, v["instr"]["mnemonic"], v["instr"]["arg1"], v["instr"]["arg2"], v["comment"])

                try:
                    file.write(new_line)
                except TypeError:
                    print(new_line)
                    break

                tmp_index += 1

        # print(comments)

        # print(labels)
if __name__ == "__main__":
    main()