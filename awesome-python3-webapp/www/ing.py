# -*- coding: utf-8 -*-
@asyncio.coroutine
def create_pool(loop,**kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host','localhost'),
        port=kw.get('port',3306)
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=lw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
        )
        
#封装Select##
@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomyssql.DictCursor)
        yield from cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('row returned:%s' % len(rs))
        return rs
        
         
 
#定义通用的函数execute()运行insert,update,delete#
@asynico.coroutine
def execute(sql,args):
    log(sql)
    with (yield from __pool) as conn:
        try:
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?','%s'),args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected
        
#编写orm＃
from orm import Model,StringField,IntegerField

class User(Model):
    __table__ = 'users'
    
    id =IntegerField(primary_key=True)
    name = StringField()
    
#定义所有orm映射的基类Model#
class Model(dict,metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)
        
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'model' object has no attribute '%s'" % key)
            
    def __setattr__(self,key,value):
        self[key] = value
        
    def getValue(self,key):
        return getattr(self,key,None)
        
    def getValueOrDefault(self,key):
        value = =getattr(self,key,None)
        if value is None:
            field = self.__mapping__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s' % (key,str(value)))
                setattr(self,key,value)
        return value
        
            
    