from socket import *
import threading # aralin pa to
import json
import time

BUFFER_SIZE = 1024
is_connected = False # initialize the connection status of the client to False

# Create client socket
client_socket = socket(AF_INET, SOCK_STREAM)

def forwardToServer(command_prompt):
    """ Forwards the command of the user to the server via sockets.
    Parameters
    ----------
    command_prompt : str
        command entered by the user 
    """

    global is_connected         # refer to the global variable 'is_connected'
    global server_address       # refer to the global variable 'server_address'
    global client_socket        # refer to the global variable 'client_socket'

    # check if the command starts with '/'
    if not command_prompt.startswith('/'):
        print('Error: Command not found. Type /? for help.')    # Error Prompt due to command syntax 
        return 
    
    # get the commands by separating the string
    inputs =  command_prompt.split()        # use the split() to separate strings
    command = inputs[0]                     # assign the command var with the first string
    params = inputs[1:]                     # assign the params list with the second string onwards

    # TODO: Implement the following commands

    # switch statement to handle commands
    match command:

        # Connect to the server application
        case '/join':
            

            # check first if the client is already connected to the server
            # if not is_connected:    
            if len(params) == 2:                    # check if there are params
                server_address = (params[0], int(params[1])) # assign the address with the params 

                try: 
                    client_socket.connect(server_address)
                    print('Connection to the File Exchange Server is successful!')

                    client_socket.send(json.dumps({'command': 'join'}).encode())

                except Exception as e:
                    print('Connection unsuccessful: ' + e)

            else:
                print('Error: Command parameters do not match or is not allowed.\nType /? for help.')

            """ else:
                print('Client is already connected. Use /leave to disconnect from the server.') """

        # Disconnect to the server application
        case '/leave':
            client_socket.send(json.dumps({'command': 'leave'}).encode())
            client_socket.shutdown(SHUT_WR)
            client_socket.close()

        # Register a unique handle or alias
        case '/register':
            pass

        # Send file to server
        case '/store':
            pass

        # Request directory file list from a server
        case '/dir':
            pass

        # Fetch a file from a server
        case '/get':
            pass

        # displays the command help 
        case '/?':
            help_prompt()
            
        # default command: handles command syntax that doesn't match pre-defined commands
        case _:
            print('Error: Command not found. Type /? for help.')    # might be redundant, test later

""" OTHER FUNCTIONS """
def help_prompt():
    """ Displays the command help to the command line interface.
    """

    print('COMMAND DESCRIPTION                          INPUT SYNTAX')
    print('Connect to the server Application            /join <server_ip_add> <port>')
    print('Disconnect to the server application         /leave')
    print('Register a unique handle or alias            /register <handle>')
    print('Send file to server                          /store <filename>')
    print('Request directory file list from a server    /dir')
    print('Fetch a file from a server                   /get <filename>')
    print('Fetch a file from a server                   /get <filename>')

# loops while the client is running to send commands to server until the client is running
while True: 
    # Get commands from the user, forwarded to the server
    command = input("\nInput Command\n> ")
    print()
    
    # use a function to forward this to the server along with the command
    forwardToServer(command)