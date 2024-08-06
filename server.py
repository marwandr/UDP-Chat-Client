import socket
import re
import logging

logging.basicConfig(
    filename='server.log',
    encoding='utf-8',
    filemode='a',
    format='{asctime} - {levelname} - {message}',
    style='{',
    datefmt='%Y-%m-%d %H:%M',
    level=logging.DEBUG
)

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 5382
HOST_PORT = (SERVER_ADDRESS, SERVER_PORT)
MAX_CLIENTS = 16
usernames = {}
loggedIn = set()

def send(MESSAGE, clientAddress, sock):                     # Function for sending messages
    string_bytes = MESSAGE.encode("utf-8")
    sock.sendto(string_bytes, clientAddress)

def findClient(username):
    for clientAddress, username1 in usernames.items():
        if username1 == username:
            return clientAddress
    return None

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(HOST_PORT)
    print("Server is on")

    while True:
        try:
            message, clientAddress = sock.recvfrom(4096)
            message = message.decode("utf-8")
            if "HELLO-FROM" in message:
                if len(loggedIn) >= MAX_CLIENTS:
                    send("BUSY\n", clientAddress, sock)
                    continue
                message = message.split(' ')
                username = ' '.join(message[1:])[:-1]
                if username in usernames.values():
                    send("IN-USE\n", clientAddress, sock)
                elif any(disallowedCharacter in username for disallowedCharacter in "!@#$%^&*") or "\n" in username:
                    send("BAD-RQST-BODY\n", clientAddress, sock)
                else:
                    usernames[clientAddress] = username
                    loggedIn.add(clientAddress)
                    send(f"HELLO {username}\n", clientAddress, sock)
            elif "LIST" in message:
                if clientAddress not in loggedIn:
                    send("BAD-RQST-HDR\n", clientAddress, sock)
                    continue
                send(f"LIST-OK {','.join(usernames.values())}\n", clientAddress, sock)
            elif "SEND" in message:
                if clientAddress not in loggedIn:
                    send("BAD-RQST-HDR\n", clientAddress, sock)
                    logging.debug("Message sent to user not logged in\n")
                    continue
                
                regex = re.search(r'^SEND (\S+) (.*)\*(\d+)\*(\d+)\n$', message)
                regex_ack = re.search(r'^SEND (\S+) ACK\n$', message)
                
                if regex:  # Handle regular message
                    recipient, msg, checksum, seq_num = regex.groups()
                    if recipient in usernames.values():
                        recipientAddress = findClient(recipient)
                        send(f"DELIVERY {usernames[clientAddress]} {msg}*{checksum}*{seq_num}\n", recipientAddress, sock)
                        send("SEND-OK\n", clientAddress, sock)
                    else:
                        logging.debug(f"Bad destination user {recipient} from {usernames[clientAddress]}")
                        send("BAD-DEST-USER\n", clientAddress, sock)

                elif regex_ack:  # Handle acknowledgment message
                    recipient = regex_ack.group(1)
                    recipientAddress = findClient(recipient)
                    if recipient in usernames.values():
                        logging.debug(f"Acknowledgment received for {recipient} from {usernames[clientAddress]}")
                        send(f"DELIVERY {recipient} ACK\n", recipientAddress, sock)
                    else:
                        send("BAD-DEST-USER\n", clientAddress, sock)
                else:
                    send("BAD-RQST-BODY\n", clientAddress, sock)
                    logging.debug(f"Failure in regex {message}\n")
                    continue
            elif "RESET" in message:
                send("SET-OK\n", clientAddress, sock)
            elif "GET" in message:
                parameter = message.split()[1]
                send(f"VALUE {parameter} 0\n", clientAddress, sock)
            elif "SET" in message:
                send("SET-OK\n", clientAddress, sock)
            else:
                send("BAD-RQST-HDR\n", clientAddress, sock)
        except Exception as e:
            logging.debug(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
