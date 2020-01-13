#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import sys
import time
import logging
import threading
import random

import socket
import hashlib
import pypinyin
    
import worker
import dbpond


cfg = worker.Config()
    
def working(cmd=''):
    if cmd == '':
        return None
    
    data = cmd.split(' ')
    if data[0] == 'help':
        showhelp()
        
    elif data[0] == 'info':
        showinfo()
        
    elif data[0] == 'userfind':
        if len(data) == 3:
            userfind(data[1][1], data[2])
        else:
            print("help:userfind -n 张三")
        
    elif data[0] == 'useradd':
        #新增用户
        if len(data)==4:
            result = useradd(data[1], data[2], data[3])
            if result is None:
                logging.info("新增失败")
            else:
                logging.info("新增成功：%s"%result)
        else:
            print("help:useradd beijing 张三 passbase")
    
    elif data[0] == 'userdel':
        #删除用户
        if len(data)==2:
            userdel(data[1])
        else:
            print("help:userdel 1000500080008150")
    
    elif data[0] == 'generate' or data[0] == 'ggg':
        #批量产生随机用户
        if len(data)==2:
            generate(int(data[1]))
        else:
            print("help:generate 100")

    else:
        print("%s: command not found"%cmd)
        
    return None


'''显示帮助信息'''
def showhelp():
    print(
"""
########################################################################
#
# 查找用户 userfind -n [用户名] -i [用户编号] -k [用户密钥] -o [办公室编号]
# userfind -n 张三
# userfind -i 1000500080102051
# userfind -k 733d7be2196ff70e1000500080102051
# userfind -o guangzhou
#
# 新增用户 useradd [办公室编号] [真实名字] [默认密码]
# useradd beijing 张三 passbase
#
# 删除用户 userdel [用户编号]
# userdel 1000500080008150
#
# 批量产生随机用户 genarate [产生数量]
# generate 21
#
# 系统信息 info [回车]
#
# 帮助信息 help [回车]
########################################################################
"""
);


'''查找用户'''
def userfind(fkey, fval):
    #print("userfind -%s %s"%(fkey, fval))
    db = dbpond.Database()
    if fkey == 'n':
        #用户名
        sql = "SELECT `id`,`userkey`,`officeid`,`realname`,`lastmac`,`addtime` FROM `smnt_client` WHERE `realname`=%s"
        result = db.fetchall(sql, (fval))
        for item in result:
            print(item[0], item[1].decode('utf8'), item[2].decode('utf8'), item[3].decode('utf8'), item[4].decode('utf8'), item[5].strftime('%F %T'))
            
    elif fkey == 'i':
        #用户编号
        pass
    elif fkey == 'k':
        #用户密钥
        pass
    elif fkey == 'o':
        #办公室编号
        pass
    else:
        print("type -%s error"%fkey)
    
'''创建一个用户'''
def useradd(officeid, realname, passbase):
    db = dbpond.Database()
    username = ''
    password = hashlib.md5(passbase.encode('utf8')).hexdigest()
    sql = "INSERT INTO `smnt_client` (`unxtime`) VALUES(UNIX_TIMESTAMP());"
    userid = db.insert(sql)
    userkey = '%s%d'%(password[:16], userid)
    sql = "UPDATE `smnt_client` SET `userkey`=%s,`officeid`=%s,`username`=%s,`realname`=%s,`password`=%s,`passbase`=%s WHERE `id`=%s;"
    result = db.execute(sql, (userkey, officeid, username, realname, password, passbase, userid))
    if result == 1:
        return userkey
    return None


'''显示系统信息'''
def showinfo():
    db = dbpond.Database()
    result = db.fetchone("SELECT COUNT(*) FROM `smnt_client`;")
    print("总用户数：%d"%result[0])
    
    result = db.fetchone("SELECT COUNT(*) FROM (SELECT COUNT(*) FROM `smnt_client` GROUP BY `officeid`) AS oids;")
    print("总办公室数：%d"%result[0])
    

'''删除一个用户'''
def userdel(userid):
    if not userid.isdigit():
        logging.warn("requireInteger:%s"%userid)
        return None
    
    db = dbpond.Database()
    result = db.execute("DELETE FROM `smnt_client` WHERE (`id`=%s)", (userid))
    if result > 0:
        logging.info("删除成功：%s"%result)
    else:
        logging.info("删除失败：%s"%result)

    return True

'''批量随机产生一堆用户'''
def generate(num, minwork=1000, maxthread=20):
    #minwork:每个线程最少搞定数量
    #maxthread:最大开启线程数
    
    assert type(num) == int

    tnum = (num+minwork-1) // minwork
    tnum = tnum if tnum > 0 else 1
    tnum = tnum if tnum < maxthread else maxthread
    tl = []
    logging.info("generate():[%d]Thread Runing..."%tnum)
    
    ework = num//tnum
    ework = num if num <= minwork else ework
    
    #logging.debug('tnum:%d'%tnum)
    #logging.debug('ework:%d'%ework)
    
    for i in range(tnum):
        #第一个线程干多一点求余
        cwork = ework
        if i == 0:
            cwork += num%(ework*tnum)
        #logging.debug('Cwork===:%d'%cwork)
        t = threading.Thread(target=usermake,args=(cwork,))
        tl.append(t)
        t.start()
        
    for i in tl:
        i.join()
    
    logging.info("generate():Generate Success,num:%d"%num)
    return None

def usermake(num):
    #logging.debug('usermake:%d'%num)
    #return None

    for i in range(num):
        now = time.time()
        #officeid, realname, passbase
        useradd(time.strftime('%Y%m%d%H%M', time.localtime(now)), '特朗普%.6f'%now, str(random.randint(100000,999999)))
    return None




if __name__ == '__main__':
    #LoggingLevel:debug[DEBUG]info[INFO]warn[WARN]error[ERROR]critical[CRITICAL]
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s>{%(levelname)s}:%(message)s')

    showhelp()

    hostname = socket.gethostname()
    while True:
        working(input("[admin@%s ~]:"%hostname))
