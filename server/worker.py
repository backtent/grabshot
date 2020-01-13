#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import pickle
import time
import configparser

import json,struct
import socket


basedir = os.path.dirname(os.path.realpath(__file__))

'''配置相关(单例设计模式)'''
class Config():
    cp = None
    
    '''
    _instance_lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        if not hasattr(Config, '_instance'):
            with Config._instance_lock:
                if not hasattr(Config, '_instance'):
                    Config._instance = object.__new__(cls)
        return Config._instance
    '''
    def __init__(self):
        cfgdir = '{basedir}{sep}conf{sep}config.ini'.format(basedir=basedir, sep=os.sep)
        self.cp = configparser.ConfigParser()
        self.cp.read(cfgdir, encoding='utf-8')

    '''获取平台号'''
    def plate(self):
        return self.cp.get('general', 'plate')
    
    '''获取通用配置'''
    def get(self, section=None, option=None, default=None):
        if section is None:#节点列表
            return self.cp.sections()
        if option is None:#值列表
            return self.cp.options(section)
        '''
        try:
            return self.cp.get(section, option)
        except configparser.NoSectionError:
            return default
        except configparser.NoOptionError:
            return default
        '''
        return self.cp.get(section, option)

    '''获取缓存路径'''
    def cache(self):
        data = self.cp.items('cache')
        plate = self.get('general', 'plate')
        print(plate)
        for item in data:
            if item[0] == plate:
                return item[1]
        return None
    
    def datas(self):
        data = {}
        sections = self.cp.sections()
        for section in sections:
            items = self.cp.items(section)
            one = {}
            for item in items:
                one[item[0]] = item[1]
            data[section]=one
        #print(data)
        return data
    
    


'''socket封装json消息包体'''
class SocketWorker():

    def __init__(self, sk):
        self.sk = sk

    '''标准socket的send'''
    def send(self, info, encoding=None):
        #print(info)
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
        #print(info)
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


    cfg = Config()
    print(cfg.cp)
    print(cfg.datas())
    print(cfg.get())
    print(cfg.get('general'))
    print("NAME:%s"%cfg.get('general', 'name'))
    print("VERSION:%s"%cfg.get('general', 'version'))
    print(cfg.cache())

    
    print("worker相关类库")
