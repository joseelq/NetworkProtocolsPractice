
import sys
import os
from socket import *
# Define dictionary of useful ASCII codes
# Use ord(char) to get decimal ascii code for char
ascii_codes = {
    "A": ord("A"), "Z": ord("Z"),
    "a": ord("a"), "z": ord("z"),
    "0": ord("0"), "9": ord("9"),
    "min_ascii_val": 0, "max_ascii_val": 127}

global port_num
global connection_exist
##############################################################################################
#                                                                                            # 
#     This function is intended to manage the command processing loop.                       #
#     The general idea is to loop over the input stream, identify which command              #
#     was entered, and then delegate the command-processing to the appropriate function.     #
#                                                                                            #
##############################################################################################
def read_commands():
    # Initially, only the CONNECT command is valid
    expected_commands = ["CONNECT"]
    previous_command = ""
    connection_exist = "NO"
    retr_counter = 0
    for command in sys.stdin:
        # Echo command exactly as it was input
        sys.stdout.write(command)

        # Extract command name from input, assuming commands are case-insensitive
        command_name = command.split()[0]

        if command.split()[0].upper() in expected_commands:
            if command_name == "CONNECT":
                response, port_num = parse_connect(command)
                # print(response)
                if "ERROR" not in response:
                    # Define port number to use to establish connection
                    # port_num = command.split()[-1]
					# global connection_exist
                    if "YES" in connection_exist:
                        # need to send a QUIT command to the Server so it can close the current socket connection
                        quit_msg = "QUIT\r\n"
                        client_socket.send(quit_msg.encode())
                        client_socket.close()
                        # Attempt to connect to Server
                        attempt, client_socket = connection_attempt(command)
                        if attempt == "ERROR":
                            print("CONNECT failed")
                            continue
                        connect_reply = client_socket.recv(1024)  # Receive data from server with buffer
                        decoded_reply = connect_reply.decode()
                        read_replies(str(decoded_reply))
                        generate_connect_output(client_socket)
                        expected_commands = ["CONNECT", "GET", "QUIT"]

                    else:
                        attempt, client_socket = connection_attempt(command)		# Attempt to Connect to Server; Server should respond if success
                        if attempt == "ERROR":
                            print("CONNECT failed")
                            continue
                        connect_reply = client_socket.recv(1024)		# Receive data from server with buffer
                        decoded_reply = connect_reply.decode()
                        read_replies(str(decoded_reply))
                        generate_connect_output(client_socket)
                        expected_commands = ["CONNECT", "GET", "QUIT"]
                        connection_exist = "YES"
            elif command_name == "GET":
                response, file_path = parse_get(command)
                if "ERROR" not in response:
                    print(response)


                    generate_get_output(port_num, file_path, client_socket)
                    port_num += 1
                    retr_counter += 1
                    expected_commands = ["CONNECT", "GET", "QUIT"]
                    previous_command = "GET"
            elif command_name == "QUIT":
                response = parse_quit(command)
                if "ERROR" not in response:
                    print(response)
                    generate_quit_output(client_socket)
                    previous_command = "QUIT"
                    connection_exist = "NO"
        else:
            print("ERROR -- Command Unexpected/Unknown")




def connection_attempt(command):
    attempt = "SUCCESS"
    host_name = sys.argv[0]
    port_number = command.split()[-1]
    # print("HOST: " + command.split()[1] + " & Port Number:" + command.split()[-1])
    # Create a TCP Socket
    try:
        client_socket = socket(AF_INET, SOCK_STREAM)		# Tell Python to help create a TCP Connection
    except:
        attempt = "ERROR"
        # print("ERROR - Failed to create socket")
        client_socket = ""
        return attempt, client_socket
    # Attempt to connect TCP Socket to Server

    try:
        client_socket.connect((command.split()[1], int(command.split()[-1])))		# create TCP connection to server at PORT 12508
    except:
        attempt = "ERROR"
        global connection_exist
        connection_exist = "NO"
        return attempt, client_socket

    print("CONNECT accepted for FTP server at host comp431-1sp21.cs.unc.edu and port " + str(port_number))		# Successful Connection
    connection_exist = "YES"
    return attempt, client_socket

##############################################################
#		FTP Reply Parse Definitions							 #
##############################################################
def read_replies(decoded_reply):
    # for reply in decoded_reply[0:]:
        # Echo the line of input (i.e., print the line of input unchanged to standard output).
    # sys.stdout.write(decoded_reply)

    # Check to see if reply is a valid FTP reply
    resp = parse_reply(str(decoded_reply))
    print(resp)


def parse_reply(reply):
    # <reply-code>
    reply, reply_code = parse_reply_code(reply)
    if "ERROR" in reply:
        return reply

    # <SP>
    reply = parse_space(reply)
    # print(reply)
    if "ERROR" in reply:
        return "ERROR -- reply-code"

    # <reply-text>
    reply, reply_text = parse_reply_text(reply)
    if "ERROR" in reply:
        return reply

    # <CRLF>
    if reply != '\r\n' and reply != '\n':
        return "ERROR -- <CRLF>"
    return "FTP reply "+ str(reply_code) + " accepted. Text is: "+ reply_text


# <reply-code> ::= <reply-number>
def parse_reply_code(reply):
    reply, reply_code = parse_reply_number(reply)
    if "ERROR" in reply:
        return "ERROR -- reply-code", reply_code
    return reply, reply_code


# <reply-number> ::= character representation of a decimal integer in the range 100-599
def parse_reply_number(reply):
    reply_number = 0
    reply = str(reply)
    if len(reply) < 3:
        return "ERROR", reply_number
    try:
        reply_number = int(reply[0:3])
    except ValueError:
        return "ERROR", reply_number
    reply_number = reply[0:3]
    if int(reply_number) < 100 or int(reply_number) > 599:
        return "ERROR", reply_number
    return reply[3:], reply_number


# <reply-text> ::= <string>
# <string> ::= <char> | <char><string>
# <char> ::= any one of the 128 ASCII characters
def parse_reply_text(reply):
    reply_text = ""
    reply = str(reply)		# got an error that object was not subscriptable
    if reply[0] == '\n' or reply[0:2] == '\r\n':
        return "ERROR -- reply_text", reply_text
    else:
        while len(reply) > 1:
            if len(reply) == 2 and reply[0:2] == '\r\n':
                return reply, reply_text
            elif ord(reply[0]) >= ascii_codes["min_ascii_val"] and ord(reply[0]) <= ascii_codes["max_ascii_val"]:
                reply_text += reply[0]
                reply = reply[1:]
            else:
                return "ERROR -- reply_text", reply_text
        return reply, reply_text


# <SP>+ ::= one or more space characters
def parse_space(reply):
    if reply[0] != ' ':
        return "ERROR"
    while reply[0] == ' ':
        reply = reply[1:]
    return reply






##############################################################
#       The following three methods are for generating       #
#       the appropriate output for each valid command.       #
##############################################################
def generate_connect_output(client_socket):
    print("USER anonymous\r\n")
    user_msg = "USER anonymous\r\n"
    try:
        client_socket.send(user_msg.encode())
    except:
        print("ERROR - failed to send USER command\r\n")		# Need to break if ERROR thrown so this doesnt always run
    user_reply = client_socket.recv(1024)
    read_replies(user_reply.decode())
    # print("FTP reply" + str(parse_reply_code(user_reply)) + " accepted: Text is: " + str(parse_reply_text(user_reply)))

    print("PASS guest@\r\n")
    pass_msg = "PASS guest@\r\n"
    try:
        client_socket.send(pass_msg.encode())
    except:
        print("ERROR - failed to send PASS command\r\n")		# Need to break if ERROR thrown so this doesnt always run
    pass_reply = client_socket.recv(1024)
    read_replies(pass_reply.decode())

    print("SYST\r\n")
    syst_msg = "SYST\r\n"
    try:
        client_socket.send(syst_msg.encode())
    except:
        print("ERROR - failed to send SYST command\r\n")		# Need to break if ERROR thrown so this doesnt always run
    syst_reply = client_socket.recv(1024)
    read_replies(syst_reply.decode())

    print("TYPE I\r\n")
    type_msg = "TYPE I\r\n"
    try:
        client_socket.send(type_msg.encode())
    except:
        print("ERROR - failed to send TYPE command\r\n")  # Need to break if ERROR thrown so this doesnt always run
    type_reply = client_socket.recv(1024)
    read_replies(type_reply.decode())

def generate_get_output(port_num, file_path, client_socket):
    try:
        my_IP = client_socket.gethostbyname(client_socket.gethostname()).replace('.', ',')
    except:
        my_IP = "127,0,0,1"
        print(my_IP)
    port_num_formatted = f"{int(int(port_num) / 256)},{int(port_num) % 256}"      # int() automatically floors its arg

    port_msg = "PORT " + str(my_IP) + "," + str(port_num_formatted) + "\r\n"
    print(port_msg)
    print(my_IP)

    # port_num used for TCP data connection is the command line argument, i.e. sys.argv[-1]


    # Lastly have to create a listening socket
    try:
        data_Socket = socket(AF_INET, SOCK_STREAM)
        with data_Socket as d:
            d.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            # print(sys.argv[-1])
            data_Socket.bind((my_IP, int(sys.argv[-1]))) # Create Welcoming TCP Socket
            data_Socket.listen(1)  # Client begins listening for incoming TCP requests, allows only 1 connection at a time
    except:
        print("GET failed, FTP-data port not allocated.")
        return  # "reads next user input line"

    # print("Send Port")
###	Send PORT command to Server ###

    try:
        client_socket.send(port_msg.encode())
    except:
        print("ERROR - failed to send PORT command")
    port_reply = client_socket.recv(1024)
    read_replies(port_reply.decode())


    ###	Send RETR command to Server ###
    retr_msg = "RETR " + str(file_path) + "\r\n"
    print(retr_msg)
    try:
        client_socket.send(retr_msg.encode())
    except:
        print("ERROR - failed to send RETR command")
    retr_reply = client_socket.recv(1024)
    print(str(retr_reply))
    read_replies(retr_reply.decode())


    # Check if ERROR, if not recieve RETR data
    if "550" in retr_reply.decode():
        return
    else:
        while True:
            try:
                connection_Socket, addr = data_Socket.accept()
            except:
                print("ERROR-failed to create FTP-data connection")
                return
            # Receive RETR data and
            while True:
                try:
                    data_recv = str(data_Socket.recv(1024).decode())
                    try:
                        shutil.copy(data_recv, "retr_files")
                        old_name = data_recv
                        new_name = "file" + str(retr_counter)
                    except:
                        print("ERROR - failed to COPY file")

                except:
                    data_Socket.close()
                    break




    print(f"PORT {my_ip},{port_num_formatted}")
    print(f"RETR {file_path}")

def generate_quit_output(client_socket):
   # print("QUIT")
    quit_msg = "QUIT\r\n"
    try:
        client_socket.send(quit_msg.encode())
    except:
        #	print("ERROR - Quit failed to send")
        a = "0"
    quit_reply = client_socket.recv(1024).decode()
    read_replies(quit_reply)
    client_socket.close()
    connection_exist = "NO"
    return connection_exist


##############################################################
#					Close current socket 	 				 #
##############################################################





##############################################################
#         Any method below this point is for parsing         #
##############################################################

# CONNECT<SP>+<server-host><SP>+<server-port><EOL>
def parse_connect(command):
    server_host = ""

    if command[0:7] != "CONNECT" or len(command) == 7:
        return "ERROR -- request", server_host
    command = command[7:]

    command = parse_space(command)
    if len(command) > 1:
        command, server_host = parse_server_host(command)
    else:
        command = "ERROR -- server-host"

    if "ERROR" in command:
        return command, server_host

    command = parse_space(command)
    if len(command) > 1:
        command, server_port = parse_server_port(command)
    else:
        command = "ERROR -- server-port"

    server_port = int(server_port)

    if "ERROR" in command:
        return command, server_host
    elif command != '\r\n' and command != '\n':
        return "ERROR -- <CRLF>", server_host
    return f"CONNECT command is valid", server_port

# GET<SP>+<pathname><EOL>
def parse_get(command):
    if command[0:3] != "GET":
        return "ERROR -- request"
    command = command[3:]

    command = parse_space(command)
    command, pathname = parse_pathname(command)

    if "ERROR" in command:
        return command
    elif command != '\r\n' and command != '\n':
        return "ERROR -- <CRLF>"
    return f"GET accepted for {pathname}", pathname

# QUIT<EOL>
def parse_quit(command):
    if command != "QUIT\r\n" and command != "QUIT\n":
        return "ERROR -- <CRLF>"
    else:
        return "QUIT accepted, terminating FTP client"

# <server-host> ::= <domain>
def parse_server_host(command):
    command, server_host = parse_domain(command)
    if command == "ERROR":
        return "ERROR -- server-host", server_host
    else:
        return command, server_host

# <server-port> ::= character representation of a decimal integer in the range 0-65535 (09678 is not ok; 9678 is ok)
def parse_server_port(command):
    port_nums = []
    port_string = ""
    for char in command:
        if ord(char) >= ascii_codes["0"] and ord(char) <= ascii_codes["9"]:
            port_nums.append(char)
            port_string += char
        else:
            break
    if len(port_nums) < 5:
        if ord(port_nums[0]) == ascii_codes["0"] and len(port_nums) > 1:
            return "ERROR -- server-port"
        return command[len(port_nums):], port_string
    elif len(port_nums) == 5:
        if ord(port_nums[0]) == ascii_codes["0"] or  int(command[0:5]) > 65535:
            return "ERROR -- server-port"
    return command[len(port_nums):], port_string

# <pathname> ::= <string>
# <string> ::= <char> | <char><string>
# <char> ::= any one of the 128 ASCII characters
def parse_pathname(command):
    pathname = ""
    if command[0] == '\n' or command[0:2] == '\r\n':
        return "ERROR -- pathname", pathname
    else:
        while len(command) > 1:
            if len(command) == 2 and command[0:2] == '\r\n':
                return command, pathname
            elif ord(command[0]) >= ascii_codes["min_ascii_val"] and ord(command[0]) <= ascii_codes["max_ascii_val"]:
                pathname += command[0]
                command = command[1:]
            else:
                return "ERROR -- pathname", pathname
        return command, pathname

# <domain> ::= <element> | <element>"."<domain>
def parse_domain(command):
    command, server_host = parse_element(command)
    return command, server_host

# <element> ::= <a><let-dig-hyp-str>
def parse_element(command, element_string=""):
    # Keep track of all elements delimited by "." to return to calling function

    # Ensure first character is a letter
    if (ord(command[0]) >= ascii_codes["A"] and ord(command[0]) <= ascii_codes["Z"]) \
    or (ord(command[0]) >= ascii_codes["a"] and ord(command[0]) <= ascii_codes["z"]):
        element_string += command[0]
        command, let_dig_string = parse_let_dig_str(command[1:])
        element_string += let_dig_string
        if command[0] == ".":
            element_string += "."
            return parse_element(command[1:], element_string)
        elif command[0] == ' ':
            return command, element_string
        else:
            return "ERROR", element_string
    elif command[0] == ' ':
        return command, element_string
    return "ERROR", element_string

# <let-dig-hyp-str> ::= <let-dig-hyp> | <let-dig-hyp><let-dig-hyp-str>
# <a> ::= any one of the 52 alphabetic characters "A" through "Z"in upper case and "a" through "z" in lower case
# <d> ::= any one of the characters representing the ten digits 0 through 9
def parse_let_dig_str(command):
    let_dig_string = ""
    while (ord(command[0]) >= ascii_codes["A"] and ord(command[0]) <= ascii_codes["Z"]) \
    or (ord(command[0]) >= ascii_codes["a"] and ord(command[0]) <= ascii_codes["z"]) \
    or (ord(command[0]) >= ascii_codes["0"] and ord(command[0]) <= ascii_codes["9"]) \
    or (ord(command[0]) == ord('-')):
        let_dig_string += command[0]
        if len(command) > 1:
            command = command[1:]
        else:
            return command, let_dig_string
    return command, let_dig_string

# <SP>+ ::= one or more space characters
def parse_space(line):
    if line[0] != ' ':
        return "ERROR"
    while line[0] == ' ':
        line = line[1:]
    return line


read_commands()
