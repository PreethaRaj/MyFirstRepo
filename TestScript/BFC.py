import struct
import socket
import ctypes
import time
import os
from ftplib import FTP
from pprint import pprint
from struct import pack, unpack
from zlib import crc32
import sys, getopt
import subprocess
import shutil
from random import randint
import filecmp
import logging
from datetime import datetime



class header:
    def __init__(self, msg_id, msg_sub_id):
        self.msg_id = msg_id
        self.msg_sub_id = msg_sub_id
        self.length = 0

    def pack(self):
        return struct.pack('>HBB', self.length, self.msg_id, self.msg_sub_id)

    def unpack(self, data):
        (self.length, self.msg_id, self.msg_sub_id) = struct.unpack('>HBB', data)

#Predefine the crc array
crc_table =[              
	0x0000,0x8911,0x1223,0x9B32,0x2446,0xAD57,0x3665,0xBF74,
	0x488C,0xC19D,0x5AAF,0xD3BE,0x6CCA,0xE5DB,0x7EE9,0xF7F8,
	0x8110,0x0801,0x9333,0x1A22,0xA556,0x2C47,0xB775,0x3E64,
	0xC99C,0x408D,0xDBBF,0x52AE,0xEDDA,0x64CB,0xFFF9,0x76E8,
	0x0221,0x8B30,0x1002,0x9913,0x2667,0xAF76,0x3444,0xBD55,
	0x4AAD,0xC3BC,0x588E,0xD19F,0x6EEB,0xE7FA,0x7CC8,0xF5D9,
	0x8331,0x0A20,0x9112,0x1803,0xA777,0x2E66,0xB554,0x3C45,
	0xCBBD,0x42AC,0xD99E,0x508F,0xEFFB,0x66EA,0xFDD8,0x74C9,
	0x0442,0x8D53,0x1661,0x9F70,0x2004,0xA915,0x3227,0xBB36,
	0x4CCE,0xC5DF,0x5EED,0xD7FC,0x6888,0xE199,0x7AAB,0xF3BA,
	0x8552,0x0C43,0x9771,0x1E60,0xA114,0x2805,0xB337,0x3A26,
	0xCDDE,0x44CF,0xDFFD,0x56EC,0xE998,0x6089,0xFBBB,0x72AA,
	0x0663,0x8F72,0x1440,0x9D51,0x2225,0xAB34,0x3006,0xB917,
	0x4EEF,0xC7FE,0x5CCC,0xD5DD,0x6AA9,0xE3B8,0x788A,0xF19B,
	0x8773,0x0E62,0x9550,0x1C41,0xA335,0x2A24,0xB116,0x3807,
	0xCFFF,0x46EE,0xDDDC,0x54CD,0xEBB9,0x62A8,0xF99A,0x708B,
	0x0884,0x8195,0x1AA7,0x93B6,0x2CC2,0xA5D3,0x3EE1,0xB7F0,
	0x4008,0xC919,0x522B,0xDB3A,0x644E,0xED5F,0x766D,0xFF7C,
	0x8994,0x0085,0x9BB7,0x12A6,0xADD2,0x24C3,0xBFF1,0x36E0,
	0xC118,0x4809,0xD33B,0x5A2A,0xE55E,0x6C4F,0xF77D,0x7E6C,
	0x0AA5,0x83B4,0x1886,0x9197,0x2EE3,0xA7F2,0x3CC0,0xB5D1,
	0x4229,0xCB38,0x500A,0xD91B,0x666F,0xEF7E,0x744C,0xFD5D,
	0x8BB5,0x02A4,0x9996,0x1087,0xAFF3,0x26E2,0xBDD0,0x34C1,
	0xC339,0x4A28,0xD11A,0x580B,0xE77F,0x6E6E,0xF55C,0x7C4D,
	0x0CC6,0x85D7,0x1EE5,0x97F4,0x2880,0xA191,0x3AA3,0xB3B2,
	0x444A,0xCD5B,0x5669,0xDF78,0x600C,0xE91D,0x722F,0xFB3E,
	0x8DD6,0x04C7,0x9FF5,0x16E4,0xA990,0x2081,0xBBB3,0x32A2,
	0xC55A,0x4C4B,0xD779,0x5E68,0xE11C,0x680D,0xF33F,0x7A2E,
	0x0EE7,0x87F6,0x1CC4,0x95D5,0x2AA1,0xA3B0,0x3882,0xB193,
	0x466B,0xCF7A,0x5448,0xDD59,0x622D,0xEB3C,0x700E,0xF91F,
	0x8FF7,0x06E6,0x9DD4,0x14C5,0xABB1,0x22A0,0xB992,0x3083,
	0xC77B,0x4E6A,0xD558,0x5C49,0xE33D,0x6A2C,0xF11E,0x780F
]


class crc:
    def __init__(self):
        self.value = 0

    def pack(self, packed_data):
        self.value = self.calculate(packed_data)
        return struct.pack('>H', self.value)

    def unpack(self, packed_data):
        (self.value) = struct.unpack('>H', packed_data)

    def calculate(self, data):
        length = len(data)
        crc = ctypes.c_ushort(0xffff)
        for i in range(0, length):
            index = (crc.value >> 8) ^ data[i]
            crc = ctypes.c_ushort(((crc.value << 8) ^ crc_table[index]))

        crc = ctypes.c_ushort(~crc.value)
        return crc.value

class dts_msg:
    def __init__(self, payload):
        self.header = header(0, 0)
        self.payload = payload
        self.crc = crc()
        pass

    def pack_data(self):        
        p = self.payload.pack()
        q = self.header.pack() + p
        return q + self.crc.pack(q)

    def set_payload_size(self, size):
        self.header.length = 6 + size

    def unpack_data(self, data):
        length = len(data)
        header_data = data[:4]
        payload_data = data[4:length-2]
        crc_data = data[length-2:]
        
        self.header.unpack(header_data)
        self.crc.unpack(crc_data)
        self.payload.unpack(payload_data)

    def pack(self):
        return b''

    def unpack(self, data):
        pass

    #Shouldn't be a member. The reader should be independent from the structure.
    def read_with_header_supplied(self, sock, header_bytes, header_struct):
        #check if lengths agree.
        if self.header.length != header_struct.length:
            print("Lengths do not agree. Expected length = {}, notified length = {}".format(self.header.length, header_struct.length))
            #return
        
        r = sock.recv(header_struct.length - 4)
        d = header_bytes + r
        self.unpack_data(d)

####################################################

class param_file:
    def __init__(self):
        self.file_id = 0x0
        self.file_name = ''
        self.version = 0
        self.path = ''

        self.length = 48

    def unpack(self, data):
        (self.file_id, self.file_name, self.version, self.path) = struct.unpack("<H12sH32s", data)
        self.file_name = self.file_name.split(b'\0', 1)[0].decode("ascii")
        self.path = self.path.split(b'\0', 1)[0].decode("ascii")

    def pack(self):
        return struct.pack('<H12sH32s', self.file_id, bytes(self.file_name, 'ascii'), self.version, bytes(self.path, 'ascii'))
        
    def output(self):
        return "file_id = {}, file_name = {}, version = {}, path = {}".format(self.file_id, self.file_name, self.version, self.path)
        
##############  REQUESTS  ##########################

class login_request(dts_msg):
    def __init__(self, client_id = '', device_type = 70, gcm_flag = 1):
        super(login_request, self).__init__(self)

        self.header.msg_id = 0x01
        self.header.msg_sub_id = 0x01
                
        self.client_id = client_id
        self.device_type = device_type
        self.gcm_flag = gcm_flag
        self.unused = 0

        self.set_payload_size(16)

    def pack(self):
        return struct.pack('<9sHBi', bytes(self.client_id, 'ascii'), self.device_type, self.gcm_flag, self.unused)

class logout_request(dts_msg):
    def __init__(self):
        super(logout_request, self).__init__(self)

        self.header.msg_id = 0x06
        self.header.msg_sub_id = 0x01

        self.set_payload_size(0)

class time_sync_response(dts_msg):
    def __init__(self):
        super(time_sync_response, self).__init__(self)

        self.header.msg_id = 0x0a
        self.header.msg_sub_id = 0x02

        self.set_payload_size(0)

class update_profile_response(dts_msg):
    def __init__(self):
        super(update_profile_response, self).__init__(self)

        self.header.msg_id = 0x11
        self.header.msg_sub_id = 0x02

        self.set_payload_size(0)

class transaction_replay_response(dts_msg):
    def __init__(self):
        super(transaction_replay_response, self).__init__(self)

        self.header.msg_id = 0x08
        self.header.msg_sub_id = 0x02

        self.no_of_files = 0
        self.no_of_replays = 0

        self.set_payload_size(4)

    def pack(self):
        return struct.pack('<HH', self.no_of_files, self.no_of_replays)

class keep_alive(dts_msg):
    def __init__(self):
        super(keep_alive, self).__init__(self)
        self.header.msg_id = 0xff
        self.header.msg_sub_id = 0x02
        
        self.set_payload_size(0)

class file_transfer_start(dts_msg):
    def __init__(self, filename='', transfer_type=1):
        super(file_transfer_start, self).__init__(self)
        self.header.msg_id = 0x0E
        self.header.msg_sub_id = 0x01
        self.file_name = filename
        self.transfer_type = transfer_type
        self.timestamp = int(time.time())

        self.set_payload_size(37)

    def pack(self):
        return struct.pack('<32sBL', bytes(self.file_name, 'ascii'), self.transfer_type, self.timestamp)

class file_transfer_end(file_transfer_start):
    def __init__(self, filename=''):
        file_transfer_start.__init__(self, filename)
        self.header.msg_id = 0x0F

class msg_data_files_uploaded_report(dts_msg):
    def __init__(self):
        super(msg_data_files_uploaded_report, self).__init__(self)

        self.header.msg_id = 0x07
        self.header.msg_sub_id = 0x01
        self.num_files = 0
        self.file_details = []

        self.set_payload_size(2)

    def pack(self):
        return struct.pack('<H', self.num_files)

class update_notification_response(dts_msg):
    def __init__(self):
        super(update_notification_response, self).__init__(self)

        self.header.msg_id = 0x05
        self.header.msg_sub_id = 0x02

        self.set_payload_size(0)

class device_auth_phase1_request(dts_msg):
    def __init__(self):
        super(device_auth_phase1_request, self).__init__(self)

        self.header.msg_id = 0x0B
        self.header.msg_sub_id = 0x01

        self.host_challenge = ''

        self.set_payload_size(8)

    def pack(self):
        return struct.pack('<8s', self.host_challenge)

class parameter_version_report(dts_msg):
    def __init__(self):
        super(parameter_version_report, self).__init__(self)

        self.header.msg_id = 0x09
        self.header.msg_sub_id = 0x01

        self.param_files = []

        self.set_payload_size(0)

    def pack(self):
        self.set_payload_size(sum([p.length for p in self.param_files]))
        buf = b''
        for p in self.param_files:
            buf = buf + p.pack()
        return buf

class logout_request(dts_msg):
    def __init__(self):
        super(logout_request, self).__init__(self)

        self.header.msg_id = 0x06
        self.header.msg_sub_id = 0x01

        self.set_payload_size(0)
        
###################### RESPONSES ##########################

class login_response(dts_msg):
    def __init__(self):
        super(login_response, self).__init__(self)
        self.ip = ''
        self.login_success = False      
            
        self.set_payload_size(16)

    def unpack(self, data):
        length = len(data)
        if length != 0: #login success.
            self.login_success = True
            self.ip = struct.unpack('<16s', data)[0]
            self.ip = self.ip.split(b'\0', 1)[0].decode("ascii")

class time_sync_request(dts_msg):
    def __init__(self):
        super(time_sync_request, self).__init__(self)
        self.time_of_req = 0
        
        self.set_payload_size(4)

    def unpack(self, data):
        self.time_of_req = struct.unpack('<L', data)[0]

class update_profile_request(dts_msg):
    def __init__(self):
        super(update_profile_request, self).__init__(self)
        self.sp_id = 0
        #self.package_id = 0
        #self.group_id = 0

        self.set_payload_size(1)

    def unpack(self, data):
        #(self.sp_id, self.package_id, self.group_id) = struct.unpack('<BBB', data)
        self.sp_id = struct.unpack('<B', data)[0]

class txn_desc:
    def __init__(self):
        self.dev_index = 0
        self.start_time = 0
        self.end_time = 0

    def unpack(self, data):
        (self.dev_index, self.start_time, self.end_time) = struct.unpack('<BLL', data)

class transaction_replay_request(dts_msg):
    def __init__(self):
        super(transaction_replay_request, self).__init__(self)
        self.msg_data_dir = ''
        self.number_of_replays = 0
        replay_list = []

    def unpack(self, data):
        self.msg_data_dir = struct.unpack('<32s', data)[0].split(b'\0', 1)[0].decode("ascii")

    def read_with_header_supplied(self, sock, header_bytes, header_struct):
        #No length check because lengths are dynamic.
        r = sock.recv(header_struct.length - 4)
        d = header_bytes + r
        self.unpack_data(d)

class file_transfer_start_response(dts_msg):
    def __init__(self):
        super(file_transfer_start_response, self).__init__(self)

        self.set_payload_size(0)

    def unpack(self, data):
        if len(data) != 0:
            print("Length should be 0 here.")

class file_transfer_end_response(file_transfer_start_response):
    def __init__(self):
        file_transfer_start_response.__init__(self)

        self.set_payload_size(0)

class msg_data_files_uploaded_response(dts_msg):
    def __init__(self):
        super(msg_data_files_uploaded_response, self).__init__(self)

        self.set_payload_size(0)
    
class update_notification_request(dts_msg):
    def __init__(self):
        super(update_notification_request, self).__init__(self)

        self.param_files = []

    def unpack(self, data):
        index = 0
        while index < len(data):
            pf = param_file()
            pf.unpack(data[index:index+48])
            self.param_files.append(pf)
            index = index + 48

    def read_with_header_supplied(self, sock, header_bytes, header_struct):
        r = sock.recv(header_struct.length - 4)
        #print("read_with_header_supplied = {}".format(r))
        d = header_bytes + r
        self.unpack_data(d)

class parameter_version_report_response(dts_msg):
    def __init__(self):
        super(parameter_version_report_response, self).__init__(self)

        self.set_payload_size(0)
        
class logout_response(dts_msg):
    def __init__(self):
        super(logout_response, self).__init__(self)

        self.set_payload_size(0)

############################################################
msg_map = {0x01 : login_response, 0x0A : time_sync_request, 0x11 : update_profile_request, 0x08 : transaction_replay_request, 0xff : keep_alive,
           0x0E : file_transfer_start_response, 0x0F : file_transfer_end_response, 0x07 : msg_data_files_uploaded_response, 0x05 : update_notification_request,
           0x09 : parameter_version_report_response, 0x06 : logout_response}

class context:
    def __init__(self):
        self.socket = None
        self.is_connected = False
        self.target_ip = ''
        self.local_param_path = ''
        self.local_txn_path = ''
        self.ftp_txn_path = ''
        self.ftp_username = ''
        self.ftp_password = ''
        self.bus_id = ''

def get_lvl1_files(path):
    return [[d, os.path.join(path, d)] for d in os.listdir(path) if os.path.isfile(os.path.join(path, d))]

def get_txn_files(path):
    return get_lvl1_files(path)

def what_to_do(msg, context):
    if msg.header.msg_id == 0x01:
        context.target_ip = msg.ip
    elif msg.header.msg_id == 0x0A:
        tsr = time_sync_response()
        print("Time sync response : {}".format(tsr.pack_data()))
        context.socket.send(tsr.pack_data())
    elif msg.header.msg_id == 0x11:
        upr = update_profile_response()
        context.socket.send(upr.pack_data())
    elif msg.header.msg_id == 0x08:
        trr = transaction_replay_response()
        context.ftp_txn_path = msg.msg_data_dir

        txn_files = [s[0] for s in get_lvl1_files(context.local_txn_path)]
        trr.no_of_files = len(txn_files)

        context.socket.send(trr.pack_data())

        current_cwd = os.getcwd()
        os.chdir(context.local_txn_path)
       
        print(context.target_ip)
        print(context.ftp_username)
        print("CREATING FTP CONNECTION...")

        ftp = FTP(context.target_ip, context.ftp_username, context.ftp_password)        
        ftp.login()

        print("Sending txn files")
        for t in txn_files:
            print("Sending {}".format(t))

            fts = file_transfer_start()
            fts.file_name = t
            fts.transfer_type = 2
            fts.timestamp = int(time.time())
            context.socket.send(fts.pack_data())

            ftp.cwd(context.ftp_txn_path)

            try:
                ftp.mkd(context.bus_id)
            except:
                print("Error creating folder in ftp")

            comp_path = os.path.join(context.ftp_txn_path, context.bus_id)
            ftp.cwd(comp_path)
            
            file = open(t, 'rb')
            print(t)
            ftp.storbinary('STOR {}'.format(t), file)

            fte = file_transfer_end()
            fte.file_name = t
            fte.transfer_type = 2
            fte.timestamp = int(time.time())
            context.socket.send(fte.pack_data())

        ftp.close()          
        
        os.chdir(current_cwd)

        mdfr = msg_data_files_uploaded_report()
        context.socket.send(mdfr.pack_data())
        
    elif msg.header.msg_id == 0xff:
        ka = keep_alive()
        context.socket.send(ka.pack_data())
    elif msg.header.msg_id == 0x0E:
        pass
    elif msg.header.msg_id == 0x0F:
        pass
    elif msg.header.msg_id == 0x07:
        pass
    elif msg.header.msg_id == 0x06:
        pass
    elif msg.header.msg_id == 0x09:
        pass
    elif msg.header.msg_id == 0x05:        
        unr = update_notification_response()
        context.socket.send(unr.pack_data())

        print("param notification : \n")
        for p in msg.param_files:
            print(p.output())

        #Move to function?

        current_cwd = os.getcwd()
        os.chdir(context.local_param_path)
        ftp = FTP(context.target_ip, context.ftp_username, context.ftp_password)
        ftp.login()
        
        for p in msg.param_files:
            param_path = os.path.join(p.path, p.file_name)
            print("Downloading {}".format(param_path))

            fts = file_transfer_start()
            fts.file_name = param_path
            fts.transfer_type = 1
            fts.timestamp = int(time.time())
            context.socket.send(fts.pack_data())
            
            ftp.retrbinary('RETR {}'.format(param_path), open(p.file_name, 'wb').write)

            fte = file_transfer_end()
            fte.file_name = param_path
            fte.transfer_type = 1
            fte.timestamp = int(time.time())
            context.socket.send(fte.pack_data())

        ftp.close()
        os.chdir(current_cwd)

        #DAGW does not handle this msg even though it is DTS doc.

        pvr = parameter_version_report()
        pvr.param_files = msg.param_files
        context.socket.send(pvr.pack_data())

        lr = logout_request()
        print("Sending logout : {}".format(lr.pack_data()))
        context.socket.send(lr.pack_data())
        
    else:
        print("Unknown msg id - {} recieved.".format(msg.header.msg_id))

def read_msg(sock, ctx):
    hd = sock.recv(4)
 
    if len(hd) == 0:
        print("Connection closed by peer.")
        ctx.is_connected = False
        sock.close()
        return None
    
    h = header(0, 0)
    h.unpack(hd)

    print("Msg received. msg_id = {}".format(h.msg_id))

    st = msg_map.get(h.msg_id)
    if st == None:
        print("Unknown msg type = {}".format(h.msg_id))

        #consume rest of msg.
        sock.recv(h.length - 4)
        
        return None

    s = st()
    s.read_with_header_supplied(sock, hd, h)
    return s

def connect_to_server(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

def simulate(host, bus_id, local_param_path, local_txn_path, ftp_username, ftp_password):

    ctx = context()
    ctx.bus_id = bus_id
    ctx.local_param_path = local_param_path
    ctx.local_txn_path = local_txn_path
    ctx.ftp_username = ftp_username
    ctx.ftp_password = ftp_password
    sock = connect_to_server(host, 7000)
    
    ctx.socket = sock
    ctx.is_connected = True

    print("Connecting Bus....")
    print(ctx.bus_id)
    print(ctx.local_param_path)
	
    if not os.path.exists(ctx.local_param_path):
       subprocess.call(r'net use * {} /user:{} {}'.format( ctx.local_param_path, "sepuser", "pass1234"), shell=True)
        #subprocess.call(r'net use * {} /user:{} {}'.format( ctx.local_param_path, "kunting", "pass1234"), shell=True)
           
    login = login_request(bus_id)
    sock.send(login.pack_data())
    while True:
        if ctx.is_connected == False:
            print("Ending loop...")
            return
        
        s = read_msg(sock, ctx)
        if s != None:
            pprint(vars(s))
            what_to_do(s, ctx)

def runbfc():
   #simulate('172.16.22.218', 'SBS5101', r'D:\SIM_FTP\Parameters', r'D:\tools\internal\Simulator\TXN_Source', 'anonymous', 'anonymous')
   #simulate('172.16.23.32', 'DAR0000', r'D:\SIM_FTP\Parameters', r'D:\SIM_FTP\Transactions', 'anonymous', 'anonymous')
   #simulate('172.16.23.32', 'DAR0001', r'D:\SIM_FTP\Parameters', r'D:\SIM_FTP\Transactions', 'anonymous', 'anonymous')  
   #simulate('172.16.23.32', 'SBS0225U', r'\\192.168.31.141\d$\simtest', r'D:\SIM_FTP\Transactions', 'anonymous', 'anonymous')
   simulate('172.16.23.32', 'SBS0225U', r'\\192.168.31.141\d$\simtest', r'D:\SIM_FTP\Transactions', 'anonymous', 'anonymous')
   simulate('172.16.23.32', 'SBS2003E',r'\\192.168.31.141\d$\simtest', r'D:\SIM_FTP\Transactions', 'anonymous', 'anonymous')
	
	


