#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import time
import json,struct
import socket
import uuid
import logging


'''客户端socket'''
class ClientWorker():
    
    def __init__(self, hostport, userkey):
        self.hostport = hostport
        self.userkey = userkey
        self.hostmac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
        self.hostname = socket.gethostname()

    def connect(self, hostport=None):
        if hostport is None:
            hostport = self.hostport
        
        while True:
            try:
                sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
                sk.settimeout(5)
                sk.connect(hostport)
            except ConnectionRefusedError as e:
                sk.close()
                logging.warning('ConnectionRefusedError reconnecting...')
                time.sleep(5)
            except:
                sk.close()
                logging.warning('Exception reconnecting...')
                time.sleep(5)
            else:
                logging.info('Connect Success')
                break
        
        self.sw = SocketWorker(sk)
        try:
            self.sw.send({'hostname':self.hostname, 'userkey':self.userkey, 'hostmac':self.hostmac}, encoding='json')
            handshake = self.sw.recv(decoding='json')
        except socket.timeout:
            logging.warn("socket timeout ...")
            self.reconnect()
            return False
        except:
            self.reconnect()
            return False
        else:
            logging.info(handshake)
            
        return True

    def reconnect(self, hostport=None):
        self.sw.close()
        self.connect(hostport)
        return True


'''socket封装json消息包体'''
class SocketWorker():

    def __init__(self, sk):
        self.sk = sk

    '''标准socket的send'''
    def send(self, info, encoding=None):
        #logging.info(info)
        if encoding == 'json':
            info = json.dumps(info)
        info = info.encode('utf-8')
        self.sk.send(struct.pack('i', len(info)))
        self.sk.send(info)
        return None
        
    '''标准socket的recv'''
    def recv(self, decoding=None):
        size = self.sk.recv(4)
        if len(size)==0:
            return None
        size, = struct.unpack('i', size)
        info = self.sk.recv(size).decode('utf-8')
        #logging.info(info)
        if decoding == 'json':
            info = json.loads(info)
        return info

    '''发送文件流'''
    def sendfile(self, fullpath):
        with open(fullpath, 'rb') as f:
            for fl in f:
                self.sk.send(fl)
                
    '''存储文件流'''
    def recvfile(self, fullpath, filesize):
        recvsize = 0
        eachsize = 1024
        with open(fullpath, 'wb') as f:
            while not recvsize == filesize:
                if filesize - recvsize < eachsize:
                    eachsize = filesize - recvsize
                b = self.sk.recv(eachsize)
                f.write(b)
                recvsize+= len(b)

    def close(self):
        return self.sk.close()





        

if __name__ == '__main__':
    #LoggingLevel:debug[DEBUG]info[INFO]warn[WARN]error[ERROR]critical[CRITICAL]
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s>{%(levelname)s}:%(message)s')

    logging.info("worker相关类库")
