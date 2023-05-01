import threading
import socket
import datetime
import os
import time
import hashlib
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_ALL = True
DEBUG= False
UDP_PORT = 5555
FILE_PACK_SIZE = 1000
HEADER_SIZE = 9 + 1 + 8 + 1 + 32
TEST = True

class udp():
    def __init__(self):
        self.token_dict = {}
        self.token_lock = threading.Lock()

    def set_token_dict(self,token,start_time):
        self.token_lock.acquire()
        self.token_dict[token] = start_time
        self.token_lock.release()

    def get_token_dict(self):
        return self.token_dict

    def udp_log(self,side, message):
        with open("udp_" + side + "_log.txt", 'a') as log:
            log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
            if LOG_ALL:
                print(message)


    def check_valid_token(self,token):
        print('got to check token- current tokens: ',self.token_dict)
        if token in self.token_dict.keys():
            time_difference = (
                        datetime.datetime.now() - datetime.datetime.strptime(self.token_dict[token], DATETIME_FORMAT)).seconds
            if time_difference < 7200:  # 2 hours
                self.token_lock.acquire()
                del self.token_dict[token]
                self.token_lock.release()
                return True
        return False


    def udp_server(self,cli_path, local_files, exit_all):
        """
        will get file request and will send Binary file data
        """

        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bind_ok = False

        try:
            udp_sock.bind(("0.0.0.0", UDP_PORT))
            bind_ok = True
            print('udp server is up')
        except socket.error as e:
            self.udp_log("server", " Sock error:" + str(e))
            if e.errno == 10048:
                self.udp_log("server", "Cant Bind  2 udp servers on same computer")

        while not exit_all and bind_ok:
            try:
                self.udp_log("server", "Go to listen")
                bin_data, addr = udp_sock.recvfrom(1024)
                data = bin_data.decode()
                if data == "":
                    continue
                if DEBUG:
                    self.udp_log("server", " Got UDP Request " + data)

                if data[:3] == "FRQ":
                    # print('got request')
                    fields = data[4:].split("|")
                    fn = fields[0]
                    fsize = int(fields[1])
                    ftoken = fields[2]
                    print(fn, fsize, ftoken)
                    if self.check_valid_token(ftoken):
                        if fn in local_files.keys():
                            if local_files[fn].size == fsize and fsize > 0:
                                fullname = os.path.join(cli_path, fn)

                                if TEST:
                                    self.udp_file_send_test(udp_sock, fullname, fsize, addr)
                                else:
                                    self.udp_file_send(udp_sock, fullname, fsize, addr)
                                time.sleep(5)
                            else:
                                self.udp_log("server", "sizes not ok")
                        else:
                            self.udp_log("server", "file not found " + fn)
                    else:
                        self.udp_log("server", "invalid token " + ftoken)
            except socket.error as e:
                print("-Sock error:" + str(e.args) + " " + e.message)
                if e.errno == 10048:
                    self.udp_log("server", "Cant Bind  2 udp servers on same computer")
                    break
                elif e.errno == 10040:
                    self.udp_log("server", "file too large")
                    continue
            except Exception as e:
                self.udp_log("server", "General error " + str(e))
                break
        udp_sock.close()
        self.udp_log("server", "udp server off")


    def udp_file_send_test(self,udp_sock, fullname, fsize, addr):
        pos = 0
        done = False
        pack_cnt = 1
        keep = {}
        with open(fullname, 'rb') as f_data:
            while not done:
                bin_data = f_data.read(FILE_PACK_SIZE)
                if len(bin_data) == 0:
                    self.udp_log("server", "Seems empty file in disk" + fullname)
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
                        self.udp_log("server", "TEST - Just sent part %d file with %d bytes header %s " % (k, len(v), v[:18]))
            udp_sock.sendto(keep[3], addr)
            udp_sock.sendto(keep[2], addr)

            if DEBUG:
                self.udp_log("server", "TEST - Just sent also 8 5 and 4 ")
        except socket.error as e:
            self.udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

        if DEBUG:
            self.udp_log("server", "End of send udp file")


    def udp_file_send(self,udp_sock, fullname, fsize, addr):
        pos = 0
        done = False
        pack_cnt = 1
        with open(fullname, 'rb') as f_data:
            while not done:
                bin_data = f_data.read(FILE_PACK_SIZE)
                if len(bin_data) == 0:
                    self.udp_log("server", "Seems empty file in disk" + fullname)
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
                        self.udp_log("server", "Just sent part %d file with %d bytes pos = %d header %s " % (
                            pack_cnt, len(bin_data), pos, bin_data[:18]))
                    pack_cnt += 1
                except socket.error as e:
                    self.udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

        if DEBUG:
            self.udp_log("server", "End of send udp file")


    def udp_file_recv(self,udp_sock, fullname, size, addr):
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
                    self.udp_log("client", "Checksum error pack " + str(pack_cnt))
                file_pos += pack_size
                if (file_pos >= size):
                    done = True

                if DEBUG and LOG_ALL:
                    self.udp_log("client", "Just got part %d file with %d bytes pos = %d header %s " % (
                        pack_cnt, len(bin_data), file_pos, header))

                if pack_cnt - 1 == last:
                    f_write.write(bin_data)
                    last += 1
                else:
                    keep[pack_cnt] = bin_data
                    if pack_cnt > max:
                        max = pack_cnt
                last = self.try_to_move_old_packs_to_file(f_write, last, max, keep)
            if file_open:
                f_write.close()
            if done:
                if os.path.isfile(fullname):
                    if os.path.getsize(fullname) == size:
                        if not checksum_error:
                            all_ok = True

        except socket.error as e:
            self.udp_log("client", "Failed to recv: " + str(e.errno))

        if all_ok:
            self.udp_log("client", "UDP Download  Done " + fullname + " len=" + str(size))
        else:
            self.udp_log("client", "Something went wrong. cant download " + fullname)


    def try_to_move_old_packs_to_file(self,f_data, last, max, keep):
        to_del = []

        for i in range(last + 1, max + 1):
            if i in keep.keys() and i - 1 == last:
                f_data.write(keep[i])
                last += 1
                to_del.append(i)
                if DEBUG:
                    self.udp_log("client", "----- Wrote old pack %d from dict ---------- " % i)
            else:
                break
        for i in to_del:
            del keep[i]

        return last


    def udp_client(self,cli_path, ip, fn, size, token):
        """
        will send file request and then will recv Binary data
        """
        # print("got to func")
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (ip, UDP_PORT)
        udp_sock.settimeout(10)
        send_ok = False

        to_send = "FRQ|" + fn + "|" + str(size) + "|" + token
        try:
            udp_sock.sendto(to_send.encode(), addr)
            send_ok = True
            if DEBUG:
                self.udp_log("client", "Sent " + to_send + " to " + addr[0] + " " + str(addr[1]))

        except socket.timeout:
            print("timeout on socket - No answer")
        except socket.error as e:
            if e.errno == 10040:
                self.udp_log("client", "Send faliled Too large file")
            else:
                self.udp_log("client", "Send faliled general socket error  " + e.message)

        if send_ok and size > 0:
            self.udp_file_recv(udp_sock, os.path.join(cli_path, fn), size, addr)

        else:
            if DEBUG:
                self.udp_log('client', "Send failed or size = 0")
        udp_sock.close()
