#!/usr/bin/env python
# coding:utf-8
import datetime
import binascii
import multiprocessing
from conf import dbConnection as db
from Crypto.Cipher import AES

#from Crypto import Random

#从配置文件中构建入口库（代码运行支撑库）连接串

#给出游标返回字典值查询结果
def rows_as_dicts(cursor):
    col_names = [i[0] for i in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor]

#给出省代码及库标识（源端还是目标端），返回到该库的连接，库中保存密文密码因此需要利用加密时的key 和iv 反解
def connecter(domainId,sysFlag,tns):
    conn = db.orcl.connect(db.dbuser,db.dbpass,tns)
    sql = "select domain_id,db_sid,db_ip,db_port,db_user,db_pass from ops_dbconnection where domain_id=:1 and sys_flag=:2"
    cur = conn.cursor()
    cur.execute(sql,(domainId,sysFlag))
    queryData = rows_as_dicts(cur)[0]
    cur.close()
    conn.close()
    if queryData.get('DB_PASS'):
        key = db.seqkey
        passwd = queryData.get('DB_PASS')
        encrypt_msg = binascii.a2b_hex(passwd)
        iv = encrypt_msg[:16]
        cipher2 = AES.new(key,AES.MODE_CFB,iv)
        decrypt_msg = cipher2.decrypt(encrypt_msg[16:])
        un_pass = decrypt_msg.decode('utf-8')
        un_user = queryData.get('DB_USER')
        #print un_pass
        un_host = queryData.get('DB_IP')
        un_port = queryData.get('DB_PORT')
        un_sid  = queryData.get('DB_SID')
        un_tns  = db.orcl.makedsn(un_host,un_port,un_sid)        
        un_conn = db.orcl.connect(un_user,un_pass,un_tns)
        return un_conn   
    else:
        return None

#比对源及目标数据库tableName 差异，测试单线程效率为为分钟600条
def comparer(domainId,srcFlag,dstFlag,tableName,tns,startId,endId,primaryKey):
    createDate = datetime.datetime.now()
    src_con = connecter(domainId, srcFlag, tns)
    dst_con = connecter(domainId, dstFlag, tns)
    #如果源与目标端连接都取到
    if src_con and dst_con:
        src_cur = src_con.cursor()
        dst_cur = dst_con.cursor()
        src_cnt_cur = src_con.cursor()
        dst_cnt_cur = dst_con.cursor()
        src_ins_cur = src_con.cursor()
        #源端取project_id，no(业务属性，与比对功能无关)
        src_sql = "select project_id,no from "+tableName+" where 1=1 and "+primaryKey+" >= :1 and "+primaryKey+" < :2"
        
        #目标端统计主键ID是否存在
        dst_sql = "select count(1) from "+tableName+" where project_id = :1"
        
        #比对关联表关联资源情况
        entity_cnt_sql = "select count(1) from rr_project_entity where project_id = :1 and substr(entity_spec_id,1,3) in (101,102,103,105,111,112,121)"
        
        #比对结果插入临时表
        ins_sql = "insert into DIF_RE_PROJECT_MSS (project_id,no,cnt_un,cnt_sm,flag,create_date) values( :1,:2,:3,:4,:5,:6)"
        
        src_cur.execute(src_sql,(startId,endId))
        
        while True:
            #每次获取200条记录
            results = src_cur.fetchmany(200)
            #如果未获取到结果退出
            if not results:
                #print datetime.datetime.now(),'比对完成！'
                break
            #处理获取取的结果集进行比对
            for rec in results:
                #取出 projectId 及 no
                projectId,noId = rec

                #针对该projectId查询目标库中该project_id是否有值，通过统计数量实现，如果没有flag为0，如果有flag > 0
                dst_cur.execute(dst_sql,(projectId,))
                flag, = dst_cur.fetchone()
                
                #统计该porjectId 在源端库中所关联的实体数量
                srcEntityCNT, = src_cnt_cur.execute(entity_cnt_sql,(projectId,)).fetchone()
                
                #如果在目标库中找到project_id，则统计目标库中该project_id所关联的实体数量
                if flag:
                    #差异类型 0  源端， 目标端库都有,判断源端和目标端该project_id关联实体数量是否一致
                    diffType  = 0
                    
                    #统计该project_id 在目标库中所关联的表中实体数量
                    dstEntityCNT, = dst_cnt_cur.execute(entity_cnt_sql,(projectId,)).fetchone()
                    
                    #如果源端关联实体数量与目标端不一致，则插入project_id 到差异表
                    if srcEntityCNT != dstEntityCNT:
                        src_ins_cur.execute(ins_sql,(projectId,noId,srcEntityCNT,dstEntityCNT,diffType,createDate))
                    else:
                        pass
                    
                #--插入 re_project_mss 表中 itspchk_ 用户有，但itsp_sm_xjx 用户没有 project_id的数据
                else:
                    #差异类型 1  源端库中有该记录，但目标库表中没有该主键记录
                    diffType = 1
                    dstEntityCNT = 0
                    src_ins_cur.execute(ins_sql,(projectId,noId,srcEntityCNT,dstEntityCNT,diffType,createDate))
                
            #遍历200条后提交一次
            src_con.commit()
    else:
        print 'Can not get the connection for database of source or destination ,please check!'
    src_cur.close()
    dst_cur.close()
    src_cnt_cur.close()
    dst_cnt_cur.close()
    src_ins_cur.close()
    src_con.close()
    dst_con.close()
    

#依据线程数量生成每线程读取的数据记录的起始ID和终止ID,因主键ID分布可能不是均匀的，
#因此采用此方法取每每段需要处理的开始及结束主键ID
def procnum(domainId,tableName,primaryKey,processNum,srcFlag,tns):
    conn = connecter(domainId, srcFlag, tns)
    if conn:
        cursor = conn.cursor()
        curRegion = conn.cursor()
        min_max_sql = "select min("+primaryKey+") as minId,max("+primaryKey+") as maxId,count(1) as total from "+tableName
        minId,maxId,total = cursor.execute(min_max_sql).fetchone()
        rangeList = []
        rows = total/processNum
        startId = minId
        regionsql = "select rn, project_id from (select rownum as rn, "+primaryKey+" from "+tableName+" order by "+primaryKey+") where mod(rn, :1) = 0"
        curRegion.execute(regionsql,(rows,))
        for rec in curRegion:
            id,endId = rec
            rangeList.append((startId,endId))
            startId = endId
        rangeList.append((startId,maxId+1))
        cursor.close()
        curRegion.close()
    else:
        pass
    conn.close()
    return rangeList
        
    
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
    mylist = procnum(domainId,tableName,primaryKey,processNum,srcFlag,tns)
    
    #定义线程池指定线程数量为5
    pool = multiprocessing.Pool(processes=5)
    

    for rec in mylist:
        startId,endId = rec
        pool.apply_async(comparer,(domainId,srcFlag,dstFlag,tableName,tns,startId,endId,primaryKey))
    pool.close()
    pool.join()
    print datetime.datetime.now()    
    print 'The program run completed!'
