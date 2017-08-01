You need create table OPS_DBCONNECTION in your assist database,like blow.The assist database connection you can configure in dbConnection.py
'''
create table OPS_DBCONNECTION
(
  id                NUMBER not null,
  domain_id         NUMBER(13) not null,
  db_entity_type    VARCHAR2(20) not null,
  db_name           VARCHAR2(40) not null,
  db_type           VARCHAR2(40),
  db_sid            VARCHAR2(40),
  db_ip             VARCHAR2(40),
  db_port           NUMBER,
  db_user           VARCHAR2(40) not null,
  db_pass           VARCHAR2(80) not null,
  enable_flag       VARCHAR2(1) not null,
  created_by        VARCHAR2(64) not null,
  creation_date     DATE default SYSDATE not null,
  last_updated_by   VARCHAR2(64),
  last_updated_date DATE,
  comments          VARCHAR2(1024),
  version           NUMBER,
  sys_flag          VARCHAR2(20)
);
'''
The OPS_DBCONNECTION record is like blow:
ID	DOMAIN_ID	DB_ENTITY_TYPE	DB_NAME	DB_TYPE	DB_SID	DB_IP	DB_PORT	DB_USER	DB_PASS	ENABLE_FLAG	CREATED_BY	CREATION_DATE	LAST_UPDATED_BY	LAST_UPDATED_DATE	COMMENTS	VERSION	SYS_FLAG
42	32	PROV_PHY_ENTITY	rmdt12pr	oracle	rmdt12pr1	10.128.xxx.xxx	3436	itsp_sm_jss	9e990dbeea9e985bf47b8f46dbb09fafd88235c10f2d0fa837f6f27d852f0f5b	Y	admin	2017/7/14 11:32:25	admin	2017/7/14 11:32:25	init user	1	sm_database
16	32	PROV_PHY_ENTITY	rmmd11pr	oracle	rmmd11pr1	10.128.xxx.xxx	3436	itspchk_js	9e990dbeea9e985bf47b8f46dbb09fafd88235c10f3d93a8837ce27c8378c2	Y	admin	2017/7/13 21:11:18	admin	2017/7/13 21:11:18	init user	1	un_database
