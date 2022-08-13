from ..util import strings as string_util;

import re;

def get_block_layer_rule(line_of_code: str) -> str:
    # Count the amount of spaces at the beginning of line_of_code
    spaces: int = 0;

    # Loop through characters in line_of_code
    for i in range(0, len(line_of_code)):
        # If the character is a space, count it
        if line_of_code[i] == " ":
            spaces += 1;
        else:
            break;

    # If space is larger than 0 return " " * spaces
    if spaces > 0:
        return " " * spaces;

    # Count the amount of tabs at the beginning of line_of_code
    tabs: int = 0;

    # Loop through characters in line_of_code
    for i in range(0, len(line_of_code)):
        # If the character is a tab, count it
        if line_of_code[i] == "\t":
            tabs += 1;
        else:
            break;

    # if tab is larger than 0 return "\t" * tabs
    if tabs > 0:
        return "\t" * tabs;

    # Throw an error if no rule is found
    raise Exception("Invalid identitation found in line of code: " + line_of_code);

def count_block_layers(line_of_code: str, rule: str) -> int:
    # Check how many leading instances of "rule" there are
    # A rule can be more than 1 character

    count: int = 0;

    # Check if rule[0] is a tab
    if rule[0] == "\t":
        seperator = "::"
        temp_string = re.sub(rule, seperator, line_of_code);

        count = len(temp_string) - len(temp_string.lstrip(seperator))

        return count;
    
    # Check if rule[0] is a space
    if rule[0] == " ":
        count = len(line_of_code) - len(line_of_code.lstrip(rule))
        count = int(count / len(rule))

        return count;

    return 0;

def deal_with_for_loops(line_of_code) -> str:
    # Any line starting with "for " belongs here

    return line_of_code;

def deal_with_colons(line_of_code) -> str:
    # Strip a clone of line_of_code
    stripped = line_of_code;
    stripped = stripped.strip();

    # Check if ":" is in line_of_code
    if ":" in line_of_code:
        # Check if line begins with "def "
        if stripped.startswith("def "):
            # Replace first instance of "def" with "local function"
            line_of_code = "\n" + re.sub(r"def ", r"local function ", line_of_code, 1);
            # Remove last instance of ":"
            line_of_code = string_util.replace_reverse(line_of_code, ":", "", 1);
        elif stripped.startswith("if ") or stripped.startswith("elif "):
            # Remove last instance of ":"
            line_of_code = string_util.replace_reverse(line_of_code, ":", "", 1);
            # Add "then"
            line_of_code = line_of_code + " then";
            # Replace elif, if exists, with "else if"
            line_of_code = re.sub(r"elif", r"else if", line_of_code, 1);
        elif stripped.startswith("else"):
            # Remove last instance of ":"
            line_of_code = string_util.replace_reverse(line_of_code, ":", "", 1);
        elif stripped.startswith("while "):
            # Replace last instance of ":" with "do"
            line_of_code = "\n" + string_util.replace_reverse(line_of_code, ":", " do", 1);
        elif stripped.startswith("for "):
            # Replace last instance of ":" with "do"
            line_of_code = "\n" + string_util.replace_reverse(line_of_code, ":", " do", 1);
            deal_with_for_loops(line_of_code);
        else:
            # Throw error
            raise Exception("An error occured at this line of code: " + line_of_code);

    return line_of_code;

def deal_with_indentation(lines: dict[str]) -> dict[str]:
    # Loop through lines
    block_rule = None;

    for i in range(0, len(lines)):
        if not isinstance(lines[i], str): continue;

        stripped = lines[i];
        stripped = stripped.strip();

        if block_rule == None and ( lines[i].startswith(" ") or lines[i].startswith("\t") ):
            try:
                block_rule = get_block_layer_rule(lines[i]);
            except Exception as e:
                error = str(e);
                break;

        lines[i] = deal_with_colons(lines[i]);

        current_block_layers: int = 0;

        if block_rule:
            current_block_layers: int = count_block_layers(lines[i], block_rule);
        
        next_block_layers: int = 0;

        # Make sure lines[i + 1] isn't out of range
        if i + 2 > len(lines): continue;

        if block_rule:
            next_block_layers: int = count_block_layers(lines[i + 1], block_rule);

        if next_block_layers == current_block_layers:
            continue;
        
        if next_block_layers > current_block_layers:
            continue;

        difference = current_block_layers - next_block_layers;

        current_relative_layer = current_block_layers;

        while difference > 0 and current_relative_layer > 0:
            current_relative_layer -= 1;
            # If next line begins with "else" and the difference is 1, continue
            next_stripped = lines[i + 1];
            next_stripped = next_stripped.strip();
            if difference == 1 and (next_stripped.startswith("else") or next_stripped.startswith("elif")): continue;

            # Add "end" underneath lines[i]
            lines[i] = lines[i] + "\n" + block_rule * (current_relative_layer) + "end";

            if difference < 2: 
                lines[i] = lines[i] + "\n"
                
            difference -= 1;

    return lines;