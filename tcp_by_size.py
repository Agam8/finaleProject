__author__ = 'Yossi'

# from  tcp_by_size import send_with_size ,recv_by_size


SIZE_HEADER_FORMAT = "000000000|" # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = True

def recv_by_size(sock):
    str_size = ""
    data_len = 0
    while len(str_size) < size_header_size:
        str_size += sock.recv(size_header_size - len(str_size)).decode()
        if str_size == "":
            break
    data  = ""
    if str_size != "":
        data_len = int(str_size[:size_header_size - 1])
        while len(data) < data_len:
            data += sock.recv(data_len - len(data)).decode()
            if data == "":
                break

    if TCP_DEBUG and str_size !="" and len(data) <= 100:
        print("\nRecv(%s)>>>%s"%(str_size, data))
    elif TCP_DEBUG and len(data) > 100:
        print("\nRecv(%s)>>>%s" % (str_size, data[:100]))

    if data_len != len(data):
        data="" # Partial data is like no data !
    return data




def send_with_size(sock, data):
    len_data = len(data)
    data = str(len(data)).zfill(size_header_size - 1) + "|" + data
    sock.send(data.encode())
    if TCP_DEBUG  and data != "" and len(data) <= 100:
        print("\nSent(%s)>>>%s" % (len_data, data))
    elif TCP_DEBUG and data != "":
        print("\nSent(%s)>>>%s"%(len_data,data[:100]))
