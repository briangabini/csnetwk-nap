from socket import *
import os
import time
import threading
import json

BUFFER_SIZE = 1024              # initialize buffer size
#exit_flag = False               # signal the thread to exit
connected_clients = []          # store the connected clients 
# disconnected_clients = []

def processCommandsFromClients(command_prompt, client_socket, client_address):
    """ This method executes the appropriate functions of the server based on the query from client/s

    PARAMETERS
    ----------
    command_prompt : str
        command entered by the user 
    client_socket: socket
        socket endpoint connected to the client
    client_address: _RetAddress
        address of the client in the form of (ip, port)
    """

    # execute this block when the command_prompt value is a json object
    try:
        
        # deserialize string to python <dict>
        data = json.loads(command_prompt.decode())      

        # assign the command
        command = data['command']   
        #print(command)         # for debugging remove this             

    # execute this block when the command_prompt value is a <dict>
    except:
        command = command_prompt['command']
        #print(command) # for debugging remove this

    # check if the command exists in the list of cases
    match command:
        
        # Close the connection in the server side
        case 'leave':
            # Close the socket connected to the client
            print(f'The client {client_address} disconnected.\n')
            client_socket.close()

            # Print to terminal the disconnection message
            
            
            #print(connected_clients) # for debugging remove this
            # Remove the disconnected client from the connected_clients list
            disconnected_client = next((client for client in connected_clients if client['address'] == client_address), None)
            if disconnected_client:
                connected_clients.remove(disconnected_client)

            #print(connected_clients) # for debugging remove this

            # Access the global var 'exit_flag' and assign True
            global exit_flag
            exit_flag = True

        # Register the client to the server by appending to the array of connected clients
        case 'register':

            # assign the handle name 
            handle = data['handle']

            # get the client from the connected_clients list based on the 'name' property
            filtered_clients = list(filter(lambda client: client['name'] == handle, connected_clients))

            # check if the client is already registered
            if filtered_clients:             

                # print the mesasge 
                print(f'User {handle} already exists.')
                response = f'User {handle} already exists. Choose a different handle.'
                client_socket.send(json.dumps({'status': 'NO', 'message': response}).encode())

            else:
                # get the client from the connected_clients list based on the 'address' property
                filtered_clients = list(filter(lambda client: client['address'] == client_address, connected_clients))

                # check if the client is already connected
                if filtered_clients:

                    # access the client's data
                    client = filtered_clients[0]

                    # assign the client's handle name to the client's existing data in the connected_clients list
                    client['name'] = handle
 
                    # initialize a response 
                    response = f'Successfully registered User {handle}'

                    # send a response to the client by using a json object that contains the status and the message 
                    client_socket.send(json.dumps({'status': 'OK', 'message': response}).encode())

                else:
                    # print the message
                    print(f'User doesn\'t exist.')

        # Send the filenames of files in the server directory to the client
        case 'dir':

            # Get all files from current directory
            dir_list = os.listdir("./")

            # Back to original dir 
            os.chdir(os.getcwd()) 

            # Remove FileServer.py from list
            dir_list.remove('FileServer.py')

            # initialize 'directory' which will be assigned with the dir_list
            directory = 'Directory: \n'

            # iterate through the dir_list and assign the filenames to 'directory'
            for file in dir_list:
                directory += f'- {file}\n'
            
            # assign the message 
            message = 'Successfully retrieved file list in directory.'

            # send the server reponse in json object notation that contains the status, message, and directory
            client_socket.send(json.dumps({'status': 'OK', 'message': message, 'directory': directory}).encode())

        case 'store':
            filename = command_prompt['filename']
                                      # Store file to server folder

            # Check if file with same file name already exists in server directory
            server_dir = os.listdir("./")
            filename = get_unique_filename(filename, server_dir)

            file_path = './' + filename    

            print('Filename: ', filename)

            file_content = command_prompt['file_content']            # get the content of a file in <bytes>

            # Get the file content
            print(file_content)

            # print('Type of file_content: ', type(file_content))

            with open(file_path, 'wb') as file:                      # write the file_content to the newly created file
                file.write(file_content)

            print(f'{client_address} successfully stored {filename} to the server.')

        case 'get':
            filename = command_prompt['filename']

            file_path = './' + filename

            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    file_content = file.read()

                    client_socket.send(str(len(file_content)).encode())     # send the file length

                    print(len(file_content))

                    time.sleep(0.1)

                    print('Type of file_content: ', type(file_content))

                    # print('file_content: ', file_content)

                    send_file(client_socket, file_content)
            
            else:
                print('Error: File does not exist.')

def get_unique_filename(file_name, server_dir):
    base, ext = os.path.splitext(file_name)
    counter = 1
    new_file_name = file_name

    while new_file_name in server_dir:
        new_file_name = f"{base}({counter}){ext}"
        counter += 1

    return new_file_name

def handle_client(client_socket, client_address):
    """ This method handles the queries sent by the client

    PARAMETERS
    ----------
    client_socket: socket
        socket endpoint connected to the client
    client_address: _RetAddress
        address of the client in the form of (ip, port)
    """
    global exit_flag        # refer to the global variable 
    # print to terminal 
    print(f"Connection established with {client_address}")
    exit_flag = False
    

    # loop until exit_flag is False
    while not exit_flag: 
        try: 

            # get the queries from the client 
            command_prompt = client_socket.recv(BUFFER_SIZE)

            # break the loop if no data is received
            if not command_prompt:
                break

            # get the command from the query
            decoded_command = command_prompt.decode()

            # check if the command is 'store'
            if decoded_command == 'store':

                # get the filename from the client                
                filename = client_socket.recv(BUFFER_SIZE).decode()

                # get the file size from the client
                file_size = int(client_socket.recv(BUFFER_SIZE).decode())

                # get the content of the file from the client
                file_content = recvall(client_socket, file_size)

                # Construct a JSON-like object
                command_data = {
                    'command': 'store',
                    'filename': filename,
                    'file_content': file_content  # Assuming file_content is a string
                }

                # Process the 'store' command with the constructed data
                processCommandsFromClients(command_data, client_socket, client_address)

            # check if the command is 'get'
            elif decoded_command == 'get':

                # get the filename from the client                
                filename = client_socket.recv(BUFFER_SIZE).decode()

                # Construct a JSON-like object
                command_data = {
                    'command': 'get',
                    'filename': filename,
                }      

                processCommandsFromClients(command_data, client_socket, client_address)

            else:
                # For other commands, process as usual
                processCommandsFromClients(command_prompt, client_socket, client_address)

        except Exception as e:
            print(f'Error handling client. {e}')
            break

""" OTHER FUNCTIONS """
def recvall(sock, size):
    """ This method executes the appropriate functions of the server based on the query from client/s

    PARAMETERS
    ----------
    sock: socket
        socket endpoint connected to the client
    size: int
        total size of the file being retrieved.
    """
    bytes_read = 0  # Keep track of the number of bytes read
    data = b"" # Stores the data being received

    # Loop until there are no more bytes left to read
    while bytes_read < size:
        packet = client_socket.recv(BUFFER_SIZE)  # Read data from the sender
        time.sleep(0.01)
        data += packet # Store data 
        bytes_read = len(data)  # Get the number of bytes read so far

    return data

def send_file(socket, file_content):
    file_position = 0
    while file_position < len(file_content):
        remaining_bytes = min(BUFFER_SIZE, len(file_content) - file_position)
        # Send a part of data to client
        socket.send(file_content[file_position:file_position + remaining_bytes])
        time.sleep(0.01)
        # Update file position
        file_position += remaining_bytes
        
# initialize the server socket 
server_socket = socket(AF_INET, SOCK_STREAM) 

# Loops until a successful server is started
while True:

    # print to terminal 
    print("FIle Transfer TCP Server")

    try:
        # ip = input("Enter IP: ")                  # user inputs IP Address for the server to bind
        # port = input("Enter Port: ")              # user inputs the Port Number for the server to bind\
        ip = "127.0.0.1"                            # hard coded for now
        port = "4000"                               # hard coded for now
        server_socket.bind((ip, int(port)))         # Bind the socket to a specific IP address and port
        server_socket.listen(1)                     # sets the maximum ammount of connections allowed 

        # print to terminal 
        print(f"Server running at {ip}:{port}")     
        break

    except Exception as e:

        # clear the terminal if there's an exception
        os.system('cls')
        print(f"Error: {str(e)}\nTry again\n")



try:      
    # Accept incoming connections  
    while True:

        # print to terminal
        print("Waiting for a connection...")

        # accept the connection from incoming clients
        client_socket, client_address = server_socket.accept()      

        # response of the server to the client
        response = "Connection established to server." 

        # send the response to the client after connecting
        client_socket.send(json.dumps({'status': 'OK', 'message': response}).encode())

        # Create a new thread for each client
        # this allows multiple tasks to run concurrently, in this case, handling multiple clients
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

        # test what will happen if we don't use threads
        # handle_client(client_socket, client_address) # only one client at a time is possible since, multiple clients will share 

        # initialize a new user 
        new_user = {'address' : client_address, 'socket': client_socket, 'name': ""}

        # Add user to list of connected clients
        connected_clients.append(new_user)

        
finally:
    #closes the server socket when done
    server_socket.close()