#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import sys
import time
import logging

import socket
import socketserver

import worker
import dbpond

basedir = os.path.dirname(os.path.realpath(__file__))


'''
使用socketserver基类
'''
class FileServer(socketserver.BaseRequestHandler):
    
    '''继承一次accept后的处理方法'''
    def handle(self):
        logging.info("[服务端]与客户端%s建立连接"%(self.client_address,))
        
        #一次accept链接会话
        sw = worker.SocketWorker(self.request)
        handshake = sw.recv(decoding='json')

        #远程套接字地址端口元组
        remotehp = self.request.getpeername()
        #握手信息
        userkey, hostmac, hostname = handshake.get('userkey'), handshake.get('hostmac'), handshake.get('hostname')
        logging.debug('%s[%s]%s'%(hostmac, userkey, hostname))
        
        if userkey is None or len(userkey)==0:
            logging.warn("userkey is empty")
            return False
        
        
        #去数据库鉴权
        db = dbpond.Database()
        result = db.fetchone("SELECT `id`,`realname` FROM `smnt_client` WHERE `userkey`=%s LIMIT 1;", userkey)
        if result is None:
            #鉴权失败:用户不存在
            sql = "INSERT INTO `smnt_client_autherr` (`userid`, `userkey`, `hostmac`, `hostname`, `content`, `remote`) VALUES (%s, %s, %s, %s, %s, %s)"
            db.insert(sql, (userkey[16:], userkey, hostmac, hostname, str(handshake), str(remotehp)))
            sw.send({'status':2, 'message':'authFailed:userNotFound'}, encoding='json')
            logging.info("authFailed:userNotFound,connectionClosed")
            return None
        else:
            #鉴权成功
            sw.send({'status':1, 'message':'authSuccess:%s'%userkey[16:]}, encoding='json')


        #记录behavior
        sql = "INSERT INTO `smnt_behavior` (`userid`, `userkey`, `action`, `content`, `hostmac`, `hostname`, `remote`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        db.insert(sql, (userkey[16:], userkey, 'logout', '用户连接成功', hostmac, hostname, str(remotehp)))
        
        userid = result[0]
        realname = result[1].decode('utf-8')

        while True:
            try:
                info = sw.recv(decoding='json')
                logging.info('%s[%s]=%s'%(realname, userid, str(info['filename'])))
                
                #时区的坑,localtime当地时区的结构化时间格式
                filetime = time.localtime(info['filetime'])
                filename = time.strftime('%Y%m%d%H%M%S', filetime)
                ymd = time.strftime('%Y%m%d', filetime)

                filedir = '{basedir}{sep}uploads{sep}{userid}{sep}{ymd}'.format(basedir=basedir, sep=os.sep, userid=userid, ymd=ymd)
                filepath = '{filedir}{sep}{filename}.png'.format(filedir=filedir, sep=os.sep, filename=filename)

                # 判断并创建目录
                if not os.path.isdir(filedir):
                    try:
                        os.makedirs(filedir)
                    except:
                        pass

                sw.recvfile(filepath, info['filesize'])

                
            except ConnectionResetError:
                logging.info("[控制台]客户主机%s强迫关闭现有连接"%(self.client_address,))
                break
            except Exception as reason:
                logging.info("[控制台]handleException:%s"%reason)
                break
            finally:
                pass
        logging.info("[控制台]与客户端%s断开连接"%(self.client_address,))

        
        #记录behavior
        sql = "INSERT INTO `smnt_behavior` (`userid`, `userkey`, `action`, `content`, `hostmac`, `hostname`, `remote`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        db.insert(sql, (userkey[16:], userkey, 'login', '用户断开连接', hostmac, hostname, str(remotehp)))













'''服务端运行入口函数'''
def runserver(hostport=None):
    if hostport is None:
        #环回地址：局域网IP
        lanip =  socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        hostport = (lanip, 8848)
        
    logging.info("[服务端]正在监听%s:%d端口..."%hostport)

    #多线程socket连接
    serv = socketserver.ThreadingTCPServer(hostport, FileServer)
    #保持服务监听线程持续
    serv.serve_forever()



if __name__ == '__main__':
    #LoggingLevel:debug[DEBUG]info[INFO]warn[WARN]error[ERROR]critical[CRITICAL]
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s>{%(levelname)s}:%(message)s')

    cfg = worker.Config()
    #print(type(cfg.get('server', 'port')))
    #print(cfg.get('general', 'debug'))

    debuging = cfg.get('general', 'debug')
    if debuging == 'ON':
        hostport = cfg.get('debuging', 'host'), int(cfg.get('debuging', 'port'))
    else:
        hostport = cfg.get('server', 'host'), int(cfg.get('server', 'port'))
    
    #监听本地的IP和端口元组
    runserver(hostport)
