#!/usr/bin/env python
#coding:utf-8

from conf import dbConnection as db

import binascii
from Crypto.Cipher import AES
from Crypto import Random



#加密过程  
#Itsp_chk#2015<---->9e990dbeea9e985bf47b8f46dbb09fafd88235c10f3d93a8837ce27c83
#Itsp_chk#2015_3<--->9e990dbeea9e985bf47b8f46dbb09fafd88235c10f3d93a8837ce27c8378c2
#
key = 'pkoss#9876543210'
passwd = '9e990dbeea9e985bf47b8f46dbb09fafd88235c10f3d93a8837ce27c83'
encrypt_msg = binascii.a2b_hex(passwd)
iv = encrypt_msg[:16]


tns = db.orcl.makedsn(db.dbhost,db.dbport,db.dbsid)
conn = db.orcl.connect(db.dbuser,db.dbpass,tns)
querysql = "select  domain_id,db_pass from ops_dbconnection t where t.sys_flag='sm_database'"
upsql = "update ops_dbconnection set db_pass = :1 where domain_id = :2 and sys_flag='sm_database'"
qucur = conn.cursor()
upcur = conn.cursor()
qset = qucur.execute(querysql)
for rec in qucur:
    domainId,dbpass = rec
    #生成密文，cipher1 对象一定要放里面，针对每个用户加密都要重新生成该对象
    cipher1 = AES.new(key,AES.MODE_CFB,iv)
    msg =  iv + cipher1.encrypt(dbpass)
    sec_dbpass = binascii.b2a_hex(msg)
    #更新密文到库中
    print 'Domain id is : ',domainId,' DataBase pass is: ',dbpass,' Security Pass is: ',sec_dbpass
    upcur.execute(upsql,(sec_dbpass,domainId))
qucur.close()
upcur.close()
conn.commit()
conn.close()

'''
cipher1 = AES.new(key,AES.MODE_CFB,iv)
encrypt_msg =  iv + cipher1.encrypt(dbpass)
sec_dbpass = binascii.b2a_hex(encrypt_msg)
'''

#解密过程
#passwd 为从数据库上读取出的加密后的字符串
# passwd = '9e990dbeea9e985bf47b8f46dbb09fafd88235c10f3d93a8837ce27c83'
# #编码转换
# encrypt_msg = binascii.a2b_hex(passwd)
# #前16位为iv
# iv = encrypt_msg[:16]
# #key 值固定
# key = 'pkoss#9876543210'
# 
# cipher2 = AES.new(key,AES.MODE_CFB,iv)
# 
# decrypt_msg = cipher2.decrypt(encrypt_msg[16:])
# #打印解密后的明文密码
# print decrypt_msg.decode('utf-8')