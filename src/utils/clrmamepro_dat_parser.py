class CMP_Dat_Parser():
    dat_string = ""
    header = {}
    games = []
    
    def __init__(self, dat_string=None):
        self.dat_string = dat_string
        
    def get_header(self):
        within_double_string = False
        start_index = 0
        nesting_level = 0
        end_index = 0
        header_dict = dict()
        key_watch = False
        value_watch = False
        
        for i, char in enumerate(self.dat_string):
            match char:
                case '"':
                    within_double_string = not(within_double_string)
                case '(':
                    if (within_double_string == False):
                        if (nesting_level == 0):
                            start_index = i + 1
                        nesting_level += 1
                case ')':
                    if (within_double_string == False):
                        nesting_level -= 1
                        if (nesting_level == 0):
                            end_index = i - 1
                            break
                case ' ':
                    if key_watch and within_double_string == False:
                        key_end_index = i
                        key_watch = False
                        value_watch = True
                        value_start_index = i + 1
                case '\n':
                    if value_watch:
                        value_watch = False
                        value_end_index = i - 1
                        key_name = self.dat_string[key_start_index:key_end_index]
                        value_data = self.dat_string[value_start_index:value_end_index]
                        header_dict[key_name] = value_data
                case _:
                    pass
            prev_char = char
            if prev_char == "\t":
                key_start_index = i+1
                key_watch = True
        for key, value in header_dict.items():
            if value[0] == '"':
                value = value[1:-1]
                header_dict[key] = value
        return header_dict
                        
if __name__ == "__main__":
    a = CMP_Dat_Parser()
    a.get_header()