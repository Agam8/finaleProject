import socket
import threading
from tcp_by_size import *
def get_data():

def main(cli_path, server_ip):
    cli_s = socket.socket()
    print("before connect ip = " + server_ip)
    cli_s.connect((server_ip, 5500))
    exit_all = False


    while True:
        if data == "q":
            break
        send_with_size(cli_s, data)

        data = recv_by_size(cli_s)
        if data == "":
            print("seems server DC")
            break
        if len(data) < 8:
            print("seems bad message format:" + data)
            break

        action = data[:8]
        fields = data[9:].split("|")
        if action == "":
            print("\n File List")
            for f in fields:
                info = f.split("~")
                print("\t" + info[0] + " " + info[1] + " " + info[2] + "\n", end=' ')
        elif action == "UPD_BACK":
            print("Got " + data)
        elif action == "LNK_BACK":
            fname = fields[0]
            fip = fields[1]
            fsize = int(fields[2])
            if fip != "0.0.0.0":
                udp_cli = threading.Thread(target=udp_client, args=(cli_path, fip, fname, fsize))
                udp_cli.start()
                print("Run udp client to download the file" + fname + " from" + fip)
                udp_cli.join()
            else:
                pass
                # Todo - ask file from server
        elif action == "RUL_BACK":
            print("Server answer and Live")
        else:
            print("Unknown action back " + action)

    cli_s.close()
    exit_all = True
    udp_srv.join()
    print("Main Client -  Bye Bye")


if __name__ == "__main__":
    if len(argv) > 2:
        main(argv[1], argv[2])
    else:
        print("USAGE : <enter client folder> <server_ip>")
        exit()
