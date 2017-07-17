#!/usr/bin/env python
# coding:utf-8
import datetime
import multiprocessing
import comparer
from conf import dbConnection as db

if __name__ == '__main__':
    tns=db.orcl.makedsn(db.dbhost,db.dbport,db.dbsid)
    domainId = 32
    #源端库标识
    srcFlag = 'un_database'
    #目标库标识
    dstFlag = 'sm_database'
    #比对的表名
    tableName = 're_project_mss'
    #比对的表的主键
    primaryKey = 'project_id'
    #定义比对该表时表中全部记录分成几段的同时比对
    processNum = 5
    print datetime.datetime.now()
    
    #comparer(domainId,srcFlag,dstFlag,tableName,tns)
    
    #获取起止project_id 段列表
    mylist = comparer.procnum(domainId,tableName,primaryKey,processNum,srcFlag,tns)
    
    #定义线程池指定线程数量为5
    pool = multiprocessing.Pool(processes=5)
    

    for rec in mylist:
        startId,endId = rec
        pool.apply_async(comparer,(domainId,srcFlag,dstFlag,tableName,tns,startId,endId,primaryKey))
    pool.close()
    pool.join()
    print datetime.datetime.now()    
    print 'The program run completed!'