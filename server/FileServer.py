from socket import *
import sys
import os
import time

server_socket = socket(AF_INET, SOCK_STREAM)

# Loops until a successful server is started
while True:
    print("FIle Transfer TCP Server")
    try:
        ip = input("Enter IP: ")
        port = input("Enter Port: ")
        server_socket.bind((ip, int(port)))        # Bind the socket to a specific IP address and port
        print(f"Server running at {ip}:{port}")
        break
    except Exception as e:
        os.system('cls')
        print(f"Error: {str(e)}\nTry again\n")