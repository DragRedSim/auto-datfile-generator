class CMP_Dat_Parser():
    dat_string = ""
    header = {}
    games = []
    
    def __init__(self, dat_string=None):
        self.dat_string = dat_string or """clrmamepro (
	name "Microsoft - Xbox - BIOS Images"
	description "Microsoft - Xbox - BIOS Images (7) (2010-09-13)"
	category Console
	version 2010-09-13
	author "Jackal | redump.org"
)

game (
	name "xbox-3944"
	description "Xbox v1.0 (Kernel Version 1.00.3944.01)"
	rom ( name xbox-3944.bin size 1048576 crc 32a9ecb6 md5 e8b39b98cf775496c1c76e4f7756e6ed sha1 67054fc88bda94e33e86f1b19be60efec0724fb6 )
)

game (
	name "xbox-4034"
	description "Xbox v1.0 (Kernel Version 1.00.4034.01)"
	rom ( name xbox-4034.bin size 1048576 crc 0d6fc88f md5 b49a417511b2dbb485aa255a32a319d1 sha1 ab676b712204fb1728bf89f9cd541a8f5a64ab97 )
)

game (
	name "xbox-4817"
	description "Xbox v1.1 (Kernel Version 1.00.4817.01)"
	rom ( name xbox-4817.bin size 1048576 crc 3f30863a md5 430b3edf0f1ea5c77f47845ed3cbd22b sha1 dc955bd4d3ca71e01214a49e5d0aba615270c03c )
)

game (
	name "xbox-5101"
	description "Xbox v1.2/v1.3/v1.4/v1.5 (Kernel Version 1.00.5101.01)"
	rom ( name xbox-5101.bin size 262144 crc e8a9224e md5 769898e9682e1f5d065b5961460d03e6 sha1 5108e1025f48071c07a6823661d708c66dee97a9 )
)

game (
	name "xbox-5530"
	description "Xbox v1.4/v1.5 (Kernel Version 1.00.5530.01)"
	rom ( name xbox-5530.bin size 262144 crc 9569c4d3 md5 e455feb286dfc16272ad94d773c24460 sha1 40fa73277013be3168135e1768b09623a987ff63 )
)

game (
	name "xbox-5713"
	description "Xbox v1.4/v1.5 (Kernel Version 1.00.5713.01)"
	rom ( name xbox-5713.bin size 262144 crc 58fd8173 md5 e27bbf815c67bcbf359907a68ea46978 sha1 8b7ccc4648ccd78cdb7b65cfca09621eaf2d4238 )
)

game (
	name "xbox-5838"
	description "Xbox v1.6 (Kernel Version 1.00.5838.01)"
	rom ( name xbox-5838.bin size 262144 crc 5be2413d md5 c5907d241de37c22b083b6e30fa934b0 sha1 b9489e883c650b5e5fe2f83a32237dbf74f0e9f1 )
)
"""
        
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
        return header_dict
                        
a = CMP_Dat_Parser()
a.get_header()