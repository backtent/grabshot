#!/usr/bin/python3
#-*-coding:utf-8-*-

import os
import sys
import time
import logging

import urllib.request
import urllib.parse
import urllib.error
import configparser


import worker

#1.检查并下载最新程序

#2.关闭程序

#3.替换程序
print(os.popen('tasklist').read())
os.system('taskkill /IM clientmnt.exe /F')


time.sleep(5)

os.system(r'C:\syscmnt\clientmnt.exe')






if __name__ == '__main__':
    #LoggingLevel:debug[DEBUG]info[INFO]warn[WARN]error[ERROR]critical[CRITICAL]
    logging.basicConfig(level=logging.INFO)
