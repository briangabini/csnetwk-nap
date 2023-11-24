from socket import *
from tabulate import tabulate
import json
import time
import os

BUFFER_SIZE = 1024          # initialize buffer size
is_connected = False        # initialize the connection status of the client to False
is_registered = False       # initialize the registered status of the client fo False

# function to create a new socket
def create_client_socket():
    return socket(AF_INET, SOCK_STREAM)

# Create client socket
client_socket = create_client_socket()

def forwardToServer(command_prompt):
    """ Forwards the command of the user to the server via sockets.
    Parameters
    ----------
    command_prompt : str
        command entered by the user 
    """

    global is_connected         # refer to the global variable 'is_connected'
    global is_registered        # refer to the global variable 'is_registered'
    global server_address       # refer to the global variable 'server_address'
    global client_socket        # refer to the global variable 'client_socket'
    
    # get the commands by separating the string
    inputs =  command_prompt.split()        # use the split() to separate strings
    command = inputs[0]                     # assign the command var with the first string
    params = inputs[1:]                     # assign the params list with the second string onwards

    # switch statement to handle commands
    match command:

        # Connect to the server application
        case '/join':
            
            # check first if the client is already connected to the server
            if not is_connected:    

                # check if there are params which consist of the ip address and port number
                if len(params) == 2:                                    
                    server_address = (params[0], int(params[1]))        # assign the address with the params 

                    try: 
                        # create a new client every time 
                        client_socket = create_client_socket()          

                        # connect the new socket with the server_address(ip, port)
                        client_socket.connect(server_address)          

                        # get the response from the server after attempting to connect to the server
                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                        # assign the message var with the message property of the response
                        message = server_response['message']

                        # print the message response sent by the server
                        print(f'Server: {message}')

                        # check if the server sent a status OK
                        if server_response['status'] == 'OK':
                            # assign the 'is_connected' var with True
                            is_connected = True
                            print(f'is_connected is now: {is_connected}')

                    except Exception as e:
                        # print error to terminal 
                        print(f'Connection unsuccessful: {e}')

                else:
                    # print error to terminal 
                    print('Error: Command parameters do not match or is not allowed.\nType /? for help.')

            else:
                # print error to terminal 
                print('Client is already connected. Use /leave to disconnect from the server.')
            
        # Disconnect to the server application
        case '/leave':

            # check if the client is connected 
            if is_connected:

                # check if the user did not input params 
                if len(params) != 0:
                    # print the error to the terminal 
                    print('Error: Command parameters do not match or is not allowed.\nUsage: /leave')

                else:
                    # send a json object that contains the command of the user 
                    client_socket.send(json.dumps({'command': 'leave'}).encode())

                    # get a response first before closing the connection
                    server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                    # assign the message var with the message property of the response
                    message = server_response['message']

                    # print the message response sent by the server
                    print(f'Server: {message}')

                    # check if the server sent a status OK
                    if server_response['status'] == 'OK':
                        # set the connection status to 'False'
                        is_connected = False

                        # set the registered status to 'False'
                        is_registered = False

                        # close the connection
                        client_socket.close()

                    # print message to terminal 
                    print(f'is_connected is now: {is_connected}')
            else:
                # print error to terminal
                print('Error. Please connect to the server first.')

        # Register a unique handle or alias
        case '/register':

            # check if the client is connected 
            if is_connected:

                # check if the user is not registered
                if not is_registered:

                    # check if the user did not input params 
                    if len(params) != 1:
                        # print the error to the terminal 
                        print('Error: Command parameters do not match or is not allowed.\nUsage: /register <handle>')

                    else:

                        client_socket.send(json.dumps({'command' : 'register', 'handle' : params[0]}).encode())

                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode()) # get the response of the server in json format

                        message = server_response['message']

                        # display server response
                        print(f'Server: {message}')

                        # check if the server responded with status 'OK'
                        if server_response['status'] == 'OK':

                            # set registered status to True
                            is_registered = True

                        else:
                            # set registered status to False
                            is_registered = False
                else:
                    # print to terminal
                    print('You can only register once.')

            else:
                # print to terminal
                print('Error: Please connect to the server first.')
            
        # Send file to server
        case '/store':

            # check if the user is connected 
            if is_connected:

                # check if the user is registered
                if is_registered:

                    # check if the user inputted params
                    if len(params) != 1:

                        # print error to terminal 
                        print('Error: Command parameters do not match or are not allowed.\nUsage: /store <filename>')

                    else:
                        # initialize the file path to the file 
                        file_path = './' + params[0] 

                        # check if the file exists
                        if os.path.exists(file_path):
                            
                            # read the file as binary and assign to 'file'
                            with open(file_path, 'rb') as file:

                                # assign the content of the file to 'file_content'
                                file_content = file.read()

                                # Signal the server that the client wants to store a file
                                client_socket.send(b'store')            

                                # pause first before sending again 
                                time.sleep(0.01)

                                # Send the filename
                                client_socket.send(params[0].encode()) 

                                # pause first before sending again 
                                time.sleep(0.01)

                                # Send the file content
                                print('Length of file: ', len(file_content))

                            # send the file to the server
                            send_file(client_socket, file_content)

                            # print success message
                            print(f'{params[0]} successfully sent to the server.')
                        
                        else:
                            # print error to terminal 
                            print('Error: File does not exist.')
                else:
                    # print error to terminal 
                    print('Error: Please register first.')

            else:
                # print error to terminal 
                print('Error: Please connect to the server first.')

        # Fetch a file from a server
        case '/get':

            # check if the user is connected
            if is_connected:

                # check if the user is registered
                if is_registered:

                    # check if the user inputted params
                    if len(params) != 1:
                        # print error to terminal 
                        print('Error: Command parameters do not match or are not allowed.\nUsage: /get <filename>')

                    else:
                        # Signal the server that the client wants to get a file
                        client_socket.send(b'get')           

                        # Send the filename
                        client_socket.send(params[0].encode())  

                        # receive the file size from the server
                        file_size = int(client_socket.recv(BUFFER_SIZE).decode())

                        # for debugging
                        # print(file_size)

                        # receive the file from the server
                        file_content = recvall(client_socket, file_size)

                    # set the filename
                    filename = params[0]

                    # Check if file with same file name already exists in server directory
                    server_dir = os.listdir("./")
                    
                    # get unique filename
                    filename = get_unique_filename(filename, server_dir)

                    # set filepath
                    file_path = './' + filename

                    # write a file and assign to 'file'
                    with open(file_path, 'wb') as file:                      
                        # write the file_content to the newly created file
                        file.write(file_content)

                        # print success message
                        print(f'Server successfully stored {filename} to the client directory.')

                else:
                    # print error to terminal 
                    print('Error: Please register first.')

            else:
                # print error to terminal 
                print('Error: Please connect to the server first.')

        # Request directory file list from a server
        case '/dir':

            # check if the user is connected
            if is_connected:

                # check if the user is registered
                if is_registered:

                    # check if there are params entered by the user
                    if len(params) != 0:

                        # print to terminal
                        print('Error: Command parameters do not match or is not allowed.\nUsage: /dir')
                    else:

                        # send the command to server via json object
                        client_socket.send(json.dumps({'command' : 'dir'}).encode())

                        # get the response from the server in object notation
                        server_response = json.loads(client_socket.recv(BUFFER_SIZE).decode())

                        directory = server_response['directory']

                        # check if the response status is OK
                        if server_response['status'] == 'OK':
                            print(directory)

                else:
                    # print to terminal
                    print('Error: Please register first')

            else:
                # print to terminal
                print('Error: Please connect to the server first.')

        # displays the command help 
        case '/?':
            help_prompt()
            
        # default command: handles command syntax that doesn't match pre-defined commands
        case _:
            print('Error: Command not found. Type /? for help.')    # might be redundant, test later

""" OTHER FUNCTIONS """
def help_prompt():
    """ 
    Display the command help in the command line interface.

    Usage:
        help_prompt()
    """

    commands = [
        ("/join", "Connect to the server application", "/join <server_ip_add> <port>"),
        ("/leave", "Disconnect from the server application", "/leave"),
        ("/register", "Register a unique handle or alias", "/register <handle>"),
        ("/store", "Send file to server", "/store <filename>"),
        ("/dir", "Request directory file list from a server", "/dir"),
        ("/get", "Fetch a file from a server", "/get <filename>")
    ]

    headers = ["Command", "Description", "Input Syntax"]

    print(tabulate(commands, headers=headers, tablefmt="fancy_grid"))

def recvall(sock, size):
    """ 
    Receive a specified amount of data from a socket.

    Parameters:
        sock (socket): The socket endpoint connected to the client.
        size (int): The total size of the data being received.

    Returns:
        bytes: The received data.

    Raises:
        Any exceptions raised during socket operations.

    Usage:
        received_data = recvall(socket_instance, total_data_size)
    """

    bytes_read = 0  # Keep track of the number of bytes read
    data = b"" # Stores the data being received

    # Loop until there are no more bytes left to read
    while bytes_read < size:

        # Read data from the sender
        packet = sock.recv(BUFFER_SIZE)

        # pause for a moment for data integrity
        time.sleep(0.01)

        # Store data 
        data += packet 

        # Get the number of bytes read so far
        bytes_read = len(data)  

    # return 'data' which contains the file data
    return data

def send_file(socket, file_content):
    """
    Send the content of a file over a socket in chunks.

    Parameters:
        socket (socket): The socket over which the file content will be sent.
        file_content (bytes): The content of the file in bytes.

    Returns:
        None

    Raises:
        Any exceptions raised during socket operations.

    Usage:
        send_file(socket_instance, file_content_bytes)
    """

    # set file position to 0
    file_position = 0

    # loop until file position is within the length of the file size
    while file_position < len(file_content):

        # assign the remaining bytes 
        remaining_bytes = min(BUFFER_SIZE, len(file_content) - file_position)

        # Send a part of data to client
        socket.send(file_content[file_position:file_position + remaining_bytes])

        # for data integrity
        time.sleep(0.01)

        # Update file position
        file_position += remaining_bytes

def get_unique_filename(file_name, server_dir):
    """
    Generate a unique filename by appending a counter to the base filename
    if a file with the same name already exists in the specified directory.

    Parameters:
        file_name (str): The original filename.
        server_dir (list): A list of existing filenames in the server directory.

    Returns:
        str: A unique filename.

    Usage:
        unique_filename = get_unique_filename("example.txt", server_directory_list)
    """

    # get the base filename, and file ext of the file
    base, ext = os.path.splitext(file_name)

    # set the counter
    counter = 1

    # assign new_file_name with original filename
    new_file_name = file_name

    # loop until successfully finding a unique filename
    while new_file_name in server_dir:

        # set new filename
        new_file_name = f"{base}({counter}){ext}"
        counter += 1

    # return the new filename
    return new_file_name


# loops while the client is running to send commands to server until the client is running
while True: 
    # Get commands from the user, forwarded to the server
    command = input("\nInput Command\n> ")
    print()
    
    # use a function to forward this to the server along with the command
    forwardToServer(command)

# TODO: do broadcasting 
# while True:
