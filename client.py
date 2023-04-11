__author__ = 'Yossi'

import datetime

import socket, time
from Shared_file import Shared_file
import hashlib

import threading, os
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
import playsound



DEBUG = True
LOG_ALL = True
TEST = False

FILE_PACK_SIZE = 1000
HEADER_SIZE = 9 + 1 + 8 + 1 + 32


def udp_log(side, message):
    with open("udp_" + side + "_log.txt", 'a') as log:
        log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
        if LOG_ALL:
            print(message)


def manu(cli_path, local_files):
    print("\n=============\n" +
          "1. DIR - show server file list\n" +
          "2. SHR - share my files \n" +
          "3. LNK - get file link \n" +
          "4. PLY - play mp3 file\n\n"
          "9. exit\n>" +
          "=============\n\n")

    data = input("Select number > ")

    if data == "9":
        return "q"
    elif data == "1":
        return "DIR"

    elif data == "2":
        d = load_local_files(cli_path)
        to_send = "SHR|" + str(len(local_files))
        for k, v in local_files.items():
            to_send += "|" + v.name + "~" + str(v.size)
        return to_send
    elif data == "3":
        fn = input("enter file name>")
        return "LNK|" + fn
    elif data == "4":
        sn = input("enter song file name>")
        play_song(cli_path, sn)
        return "RULIVE"

    else:
        return "RULIVE"


def play_song(cli_path, song_name):
    print(f"playing {song_name} from your library")
    playsound.playsound(os.path.join(cli_path, song_name))


def load_local_files(cli_path):
    d = {}
    for f in os.listdir(cli_path):
        full_name = os.path.join(cli_path, f)
        if DEBUG:
            print("f " + full_name + " " + str(os.path.isfile(full_name)))
        if os.path.isfile(full_name):
            d[f] = Shared_file(f, os.path.getsize(full_name), "!")
    return d


def udp_server(cli_path, local_files, exit_all):
    """
    will get file request and will send Binary file data
    """

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bind_ok = False

    try:
        udp_sock.bind(("0.0.0.0", 5501))
        bind_ok = True
        print('udp server is up')
    except socket.error as e:
        udp_log("server", " Sock error:" + str(e))
        if e.errno == 10048:
            udp_log("server", "Cant Bind  2 udp servers on same computer")

    while not exit_all and bind_ok:
        try:
            udp_log("server", "Go to listen")
            bin_data, addr = udp_sock.recvfrom(1024)
            data = bin_data.decode()
            if data == "":
                continue
            if DEBUG:
                udp_log("server", " Got UDP Request " + data)
            if data[:3] == "FRQ":
                print('got request')
                fields = data[4:].split("|")
                fn = fields[0]
                fsize = int(fields[1])

                if fn in local_files.keys():
                    if local_files[fn].size == fsize and fsize > 0:
                        fullname = os.path.join(cli_path, fn)

                        if TEST:
                            udp_file_send_test(udp_sock, fullname, fsize, addr)
                        else:
                            udp_file_send(udp_sock, fullname, fsize, addr)
                        time.sleep(5)
                    else:
                        udp_log("server", "sizes not ok")
                else:
                    udp_log("server", "file not found " + fn)
        except socket.error as e:
            print("-Sock error:" + str(e.args) + " " + e.message)
            if e.errno == 10048:
                udp_log("server", "Cant Bind  2 udp servers on same computer")
                break
            elif e.errno == 10040:
                udp_log("server", "file too large")
                continue
        except Exception as e:
            udp_log("server", "General error " + str(e))
            break
    udp_sock.close()
    udp_log("server", "udp server off")


def udp_file_send_test(udp_sock, fullname, fsize, addr):
    pos = 0
    done = False
    pack_cnt = 1
    keep = {}
    with open(fullname, 'rb') as f_data:
        while not done:
            bin_data = f_data.read(FILE_PACK_SIZE)
            if len(bin_data) == 0:
                udp_log("server", "Seems empty file in disk" + fullname)
                break
            pos += len(bin_data)
            if pos >= fsize:
                done = True
            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            header = (str(len(bin_data)).zfill(9) + "," + str(pack_cnt).zfill(8) + "," + checksum).encode()
            bin_data = header + bin_data
            keep[pack_cnt] = bin_data
            pack_cnt += 1

    try:
        for k, v in keep.items():
            if k != 2 and k != 3:
                udp_sock.sendto(v, addr)
                if DEBUG and LOG_ALL:
                    pass
                    udp_log("server", "TEST - Just sent part %d file with %d bytes header %s " % (k, len(v), v[:18]))
        udp_sock.sendto(keep[3], addr)
        udp_sock.sendto(keep[2], addr)

        if DEBUG:
            udp_log("server", "TEST - Just sent also 8 5 and 4 ")
    except socket.error as e:
        udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

    if DEBUG:
        udp_log("server", "End of send udp file")


def udp_file_send(udp_sock, fullname, fsize, addr):
    pos = 0
    done = False
    pack_cnt = 1
    with open(fullname, 'rb') as f_data:
        while not done:
            bin_data = f_data.read(FILE_PACK_SIZE)
            if len(bin_data) == 0:
                udp_log("server", "Seems empty file in disk" + fullname)
                break
            pos += len(bin_data)
            if (pos >= fsize):
                done = True

            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            header = (str(len(bin_data)).zfill(9) + "," + str(pack_cnt).zfill(8) + "," + checksum).encode()
            bin_data = header + bin_data
            try:
                udp_sock.sendto(bin_data, addr)
                if DEBUG and LOG_ALL:
                    pass
                    udp_log("server", "Just sent part %d file with %d bytes pos = %d header %s " % (
                        pack_cnt, len(bin_data), pos, bin_data[:18]))
                pack_cnt += 1
            except socket.error as e:
                udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

    if DEBUG:
        udp_log("server", "End of send udp file")


def udp_file_recv(udp_sock, fullname, size, addr):
    done = False
    file_pos = 0
    last = 0
    max = 0
    keep = {}
    file_open = False
    all_ok = False
    checksum_error = False
    try:

        while not done:
            data = b""
            while len(data) < HEADER_SIZE:
                rcv_data, addr = udp_sock.recvfrom(FILE_PACK_SIZE + HEADER_SIZE)
                if rcv_data == b"":
                    return False
                data += rcv_data
            if data == "":
                return False
            if not file_open:
                f_write = open(fullname, 'wb')
                file_open = True

            header = data[:HEADER_SIZE].decode()
            pack_size = int(header[:9])
            pack_cnt = int(header[10:18])
            pack_checksum = header[19:]
            bin_data = data[HEADER_SIZE:]
            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            if checksum != pack_checksum:
                checksum_error = True
                udp_log("client", "Checksum error pack " + str(pack_cnt))
            file_pos += pack_size
            if (file_pos >= size):
                done = True

            if DEBUG and LOG_ALL:
                pass
                udp_log("client", "Just got part %d file with %d bytes pos = %d header %s " % (
                    pack_cnt, len(bin_data), file_pos, header))

            if pack_cnt - 1 == last:
                f_write.write(bin_data)
                last += 1
            else:
                keep[pack_cnt] = bin_data
                if pack_cnt > max:
                    max = pack_cnt
            last = try_to_move_old_packs_to_file(f_write, last, max, keep)
        if file_open:
            f_write.close()
        if done:
            if os.path.isfile(fullname):
                if os.path.getsize(fullname) == size:
                    if not checksum_error:
                        all_ok = True

    except socket.error as e:
        udp_log("client", "Failed to recv: " + str(e.errno))

    if all_ok:
        udp_log("client", "UDP Download  Done " + fullname + " len=" + str(size))
    else:
        udp_log("client", "Something went wrong. cant download " + fullname)


def try_to_move_old_packs_to_file(f_data, last, max, keep):
    to_del = []

    for i in range(last + 1, max + 1):
        if i in keep.keys() and i - 1 == last:
            f_data.write(keep[i])
            last += 1
            to_del.append(i)
            if DEBUG:
                udp_log("client", "----- Wrote old pack %d from dict ---------- " % i)
        else:
            break
    for i in to_del:
        del keep[i]

    return last


def udp_client(cli_path, ip, fn, size):
    """
    will send file request and then will recv Binary data
    """
    # print("got to func")
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (ip, 5501)
    udp_sock.settimeout(10)
    send_ok = False

    to_send = "FRQ|" + fn + "|" + str(size)
    try:

        udp_sock.sendto(to_send.encode(), addr)
        send_ok = True
        if DEBUG:
            udp_log("client", "Sent " + to_send + " to " + addr[0] + " " + str(addr[1]))

    except socket.timeout:
        print("timeout on socket - No answer")
    except socket.error as e:
        if e.errno == 10040:
            udp_log("client", "Send faliled Too large file")
        else:
            udp_log("client", "Send faliled general socket error  " + e.message)

    if send_ok and size > 0:

        udp_file_recv(udp_sock, os.path.join(cli_path, fn), size, addr)

    else:
        if DEBUG:
            udp_log('client', "Send failed or size = 0")
    udp_sock.close()


def main(cli_path, server_ip):
    cli_s = socket.socket()

    local_files = load_local_files(cli_path)
    print("before connect ip = " + server_ip)
    cli_s.connect((server_ip, 5500))
    exit_all = False
    udp_srv = threading.Thread(target=udp_server, args=(cli_path, local_files, exit_all))
    udp_srv.start()
    time.sleep(0.3)

    while True:
        data = manu(cli_path, local_files)

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
        if action == "DIR_BACK":
            print("\n File List")
            for f in fields:
                info = f.split("~")
                if len(info) > 1:
                    print("\t" + info[0] + " " + info[1] + " " + info[2] + "\n", end=' ')
                else:
                    print("\tserver's directory is empty\n")
        elif action == "SHR_BACK":
            print("Share status: " + data)
        elif action == "UPD_BACK":
            print("Got " + data)
        elif action == "LNK_BACK":
            fname = fields[0]
            fip = fields[1]
            fsize = int(fields[2])
            if fip != "0.0.0.0":
                print('got to udp client')
                udp_cli = threading.Thread(target=udp_client, args=(cli_path, fip, fname, fsize))
                udp_cli.start()
                print("Run udp client to download the file " + fname + " from " + fip)
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

"""
def udp_file_recv2(udp_sock, fullname, size, addr):
    done = False
    file_pos = 0
    last = 0
    max = 0
    keep = {}

    with open(fullname,'wb') as f_data:

        while not done:
            header = ""
            while len(header) < HEADER_SIZE:
                rcv_data, addr = udp_sock.recvfrom(HEADER_SIZE - len(header) )
                if rcv_data == "":
                    return False
                header += rcv_data
            if header == "":
                return False
            pack_size = int(header[:9])
            pack_cnt = int(header[10:18])

            recv_data = ""
            while len(recv_data) < pack_size:
                data , addr = udp_sock.recvfrom(pack_size - len(recv_data))
                recv_data += data
                if data == "":
                     return False
            file_pos +=   pack_size
            if (file_pos >= size):
                done = True

            if pack_cnt > max:
                    max = pack_cnt
            if pack_cnt - 1  == last:
                f_data.write(rcv_data)
                last += 1
            else:
                keep[pack_cnt] = rcv_data
                if DEBUG:
                    print "Got unorder pack number " + str (pack_cnt)

            last = try_to_move_old_packs_to_file(f_data,last,max, keep)
    if DEBUG:
        if os.path.isfile(fullname):
            if os.path.getsize(fullname) == size:
                print "Got Udp file" + fullname + " len=" + str(size)
        else:
            print "Udp client - Something went wrong cant download " + fullname

"""
