
import sys
import os
import re

# Define important ASCII character decimal representations
# These are helpful for defining various command grammars  
# Use ord(char) to get decimal ascii code for char
cr = ord('\r')  # = 13
lf = ord('\n')  # = 10
crlf_vals = [cr, lf]
sp = ord(' ')  # = 32
co = ord(",")  # = 44
pd = ord(".")  # = 46

counter = 0

valid_user = "None"
valid_pair = "None"

# Define known server commands (case insensitive). Add to this as commands are added
command_list = ["USER", "PASS", "TYPE", "SYST", "NOOP", "QUIT", "PORT", "RETR"]

# Manage valid response messages for every command
valid_responses = {
	"USER": "331 Guest access OK, send password.\r\n",
	"PASS": "230 Guest login OK.\r\n",
	"SYST": "215 UNIX Type: L8.\r\n",
	"TYPE I": "200 Type set to I.\r\n",
	"TYPE A": "200 Type set to A.\r\n",
	"PORT": "200 Port command successful.\r\n",
	"RETR": "250 Requested file action completed.\r\n",
	"NOOP": "200 Command OK.\r\n",
	"QUIT": "200 Command OK.\r\n"

}

valid_responses_type = {
	"I": "200 Type set to I.\r\n",
	"A": "200 Type set to A.\r\n"
}


##############################################################################################
#                                                                                            # 
#     This function is intended to manage the command processing loop.                       #
#     The general idea is to loop over the input stream, identify which command              #
#     was entered, and then delegate the command-processing to the appropriate function.     #
#                                                                                            #
##############################################################################################
def read_commands():
	# FTP service always begins with "220 COMP 431 FTP server ready.\r\n"
	sys.stdout.write("220 COMP 431 FTP server ready.\r\n")

	# Keep track of the expected commands, initially only "USER" and "QUIT" are valid commands
	expected_commands = ["USER", "QUIT"]
	for command in sys.stdin:  # Iterate over lines from input stream until EOF is found
		# Echo the line of input
		sys.stdout.write(command)

		# Split command into its tokens and parse relevant command
		tokens = command.split()  # Assume tokens are delimited by <SP>, <CR>, <LF>, or <CRLF>

		# Check to make sure there are tokens in the line, and assign command_name
		command_name = tokens[0].upper() if len(tokens) > 0 else "UNKNOWN"  # Commands are case-insensitive
		# Check first token in list to see if it matches any valid commands
		if command_name in command_list and not command[0].isspace():
			if command_name in expected_commands:
				#############################################################
				#  This is intended to delegate command processing to       #
				#  the appropriate helper function. Helper function parses  #
				#  command, performs any necessary work, and returns        #
				#  updated list of expected commands                        #
				#############################################################
				# if no valid user, then only accept USER or Pass
				if valid_user == "None" and command_name != "USER":
					sys.stdout.write("530 Not logged in.")

				if command_name == "USER":
					if valid_pair == "None":
						# if counter = 1,#500 Syntax error, command unrecognized, after 1st valid USER/PASS pair, dont accept more
						result, expected_commands = parse_user(tokens)
					else:
						result = "500 Syntax error, command unrecognized"

				if command_name == "PASS":
					if valid_pair == "None":
						result, expected_commands = parse_pass(tokens)
					else:
						result = "500 Syntax error, command unrecognized."

				if command_name == "SYST":
					result, expected_commands = parse_syst(tokens)

				if command_name == "TYPE":
					result, expected_commands = parse_type(tokens)

				if command_name == "NOOP":
					result, expected_commands = parse_noop(tokens)

				if command_name == "QUIT":
					result, expected_commands = parse_quit(tokens)

				if command_name == "PORT":
					result, expected_commands = parse_port(tokens)

				##################################################
				#  After command processing, the following code  #
				#  prints the appropriate response message       #

				if result != "ok":
					sys.stdout.write(result)
				else:
					if (ord(command[-1]) == lf and ord(command[-2]) == cr) or ord(command[-1]) == lf:

						# if TYPE command, check if it is either "I"/"A" and then write appropriate response
						if command_name == "TYPE":
							if tokens[1] == "I":
								sys.stdout.write(valid_responses_type["I"])
							else:
								sys.stout.write(valid_responses_type["A"])
						if command_name == "PORT":
							sys.stdout.write(valid_responses[command_name] + '(' + tokens[1:4] + '.' + z + ')')

						else:
							sys.stdout.write(valid_responses[command_name])
					else:
						sys.stdout.write("501 Syntax error in parameter(1).\r\n")
						######################################################
						#  Update expected_commands list if incorrect CRLF   #
						#  changes the possible commands that can come next  #
						######################################################
						if command_name == "USER":
							expected_commands = ["USER", "QUIT"]
						if command_name == "PASS":
							expected_commands = ["PASS", "USER", "QUIT"]
						if command_name == "SYST":
							expected_commands = ["TYPE", "SYST", "NOOP", "PORT", "QUIT"]
						if command_name == "TYPE":
							expected_commands = ["TYPE", "SYST", "NOOP", "PORT", "QUIT"]
						if command_name == "NOOP":
							expected_commands = ["NOOP", "QUIT", "SYST", "TYPE", "PORT"]
						if command_name == "QUIT":
							expected_commands = ["QUIT", "NOOP", "SYST", "TYPE", "PORT"]
			else:
				# Out of order command received
				sys.stdout.write("503 Bad sequence of commands.\r\n")
		else:
			# No valid command was input
			sys.stdout.write("500 Syntax error, command unrecognized.\r\n")


################################################################################
#                                                                              # 
#     Parse the USER command to check if tokens adhere to grammar              #
#     The "tokens" parameter is a list of the elements of the command          #
#     separated by whitespace. The return value indicates if the command       #
#     is valid or not, as well as the next list of valid commands.             #
#                                                                              #
################################################################################
def parse_user(tokens):
	# Check to make sure there is at least one token after "USER"
	if len(tokens) == 1:
		return "501 Syntax error in parameter(2).\r\n", ["USER", "QUIT"]
	else:
		# Iterate through remaining tokens and check that no invalid usernames are entered
		for token in tokens[1:]:
			for char in token:
				if ord(char) > 127 or ord(
						char) in crlf_vals:  # Byte values > 127 along with <CRLF> are not valid for usernames
					return "501 Syntax error in parameter(3).\r\n", ["USER", "QUIT"]
	# if USER is valid, save it as the most recent USER
	global valid_user
	valid_user = tokens[1]
	return "ok", ["USER", "PASS",
				  "QUIT"]  # If the function makes it here, the input adheres to the grammar for this command


def parse_pass(tokens):
	# Check to make sure there is at least one token after "PASS"
	if len(tokens) == 1:
		return "501 Syntax error in parameter.\r\n", ["USER", "PASS", "QUIT"]
	else:
		for token in tokens[1:]:
			# iterate through remaining tokens and check that no invalid passwords are entered
			for char in token:
				if ord(char) > 127 or ord(char) in crlf_vals:
					# if password is invalid, then next expected command is USER,PASS,QUIT
					return "501 Syntax error in parameter.\r\n", ["USER", "PASS", "QUIT"]
	global valid_pair
	valid_pair = tokens[1]
	# Valid PASS must precede any other (non-USER) command
	return "ok", ["USER", "SYST", "NOOP", "TYPE", "PORT", "QUIT"]


def parse_syst(tokens):
	if len(tokens) == 1:
		return "ok", ["SYST", "TYPE I", "TYPE A", "NOOP", "PORT", "QUIT"]
	else:
		return "501 Sytax error in parameter.", ["SYST", "TYPE I", "TYPE A", "NOOP", "PORT", "QUIT"]


def parse_type(tokens):
	if len(tokens) != 2:
		return "501 Syntax error in parameter.", ["TYPE", "PORT", "NOOP", "SYST", "QUIT"]
	else:
		if tokens[1] == "I" or tokens[1] == "i":
			return "ok", ["SYST", "TYPE" "PORT", "QUIT", "NOOP"]

		if tokens[1] == "A" or tokens[1] == "a":
			return "ok", ["SYST", "TYPE" "PORT", "QUIT", "NOOP"]


def parse_noop(tokens):
	if len(tokens) != 1:
		return "501 Syntax error in parameter.", ["TYPE", "PORT", "NOOP", "SYST", "QUIT"]
	else:
		return "200 Command OK", ["TYPE", "PORT", "NOOP", "SYST", "QUIT"]


def parse_quit(tokens):
	if len(tokens) != 1:
		return "501 Syntax error in parameter.", ["TYPE", "PORT", "NOOP", "SYST", "QUIT"]
	else:
		return "ok", []


def parse_port(tokens):
	# PORT 152, 2, 131, 205, 31, 144
	# split the PORT text into its tokens ["PORT", '152', '2', '131', '205', '31', '144']
	tokens_port = re.split('  | ,', tokens)

	if len(tokens_port) != 7:
		return "501 Syntax error in parameter.", ["PORT", "SYST", "TYPE", "NOOP", "QUIT"]
	else:
		# cif len(tokens_port[1]) == 3 and len(tokens_port[2]) == 1 and len(tokens_port[3]) == 3 and len(tokens_port[4]) == 3 and len(tokens_port[5]) == 2 and len(tokens_port[6]) == 3:
		# iterate through each char of each token and check if any invalid values were inputted
		for token in tokens_port[1:]:
			for char in token:
				# char must be a number and not be one of the cr_lf vals
				if ord(char) < 48 or ord(char) > 57 or ord(char) in crlf_vals:
					return "501 Syntax error in parameter.", ["PORT", "SYST", "TYPE", "NOOP", "QUIT"]
	# convert last two numbers into corresponding decimal value
	global z
	x = int(tokens_port[5]) * 256
	y = int(tokens_port[6])
	z = x + y

	# replace the commas with periods in the IP Address, i.e., 152,2,131,205 -> 152.2.131.205
	tokens = tokens.replace(',', '.')

	return "ok", ["RETR", "SYST", "TYPE", "NOOP", "QUIT"]


read_commands()

