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
        value = getattr(self,key,None)
        if value is None:
            field = self.__mapping__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s' % (key,str(value)))
                setattr(self,key,value)
        return value
        
#定义Filed and Filed的子类#
class Field(object):
    def __init__(self,name,column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        
    def __str__(self):
        return '<%s,%s:%s>' % (self.__clasee__.__name__,self.column_type,self.name)
        
class StringField(Field):
    
    def __init__(self,name=None,primary_key=False,default=None,ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)
        
class ModelMetaclass(type):
    
    def __new__(cls,name,bases,attrs):
        #排除Model类本身
        if name=='Model':
            return type.__new__(cls,name,bases,attrs)
        #获取table名称：
        tableName = attrs.get('__table__',None) or name
        logging.info('found model:%s (table:%s)'%(name,tableName))
        #获取所有的Field和主键名：
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info(' found mpping:%s ==>%s'%(k,v))
                mapping[k] = v
                if v.primary_key:
                    #找到主键:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field:%s' %k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('primary key not found.')
        for k in mapping.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mapings__'] = mapping #保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey #主键属性名
        attrs['__fields__'] = fields #除主键外的属性名
        #构造默认的select,insert,update和DELETE语句：
        attrs[__'select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)
        
 #这样，任何继承自Model的类（比如user），会自动通过ModelMtaclass扫描映射关系，并存储到自身的雷属性如__table__/__mappings__中
    
            
    