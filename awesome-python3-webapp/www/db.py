# -*- coding: utf-8 -*-
#db.py

#数据库引擎对象
class _Engine(object):
    def __init__(self,connect):
        self._connect = connect
    def connect(self):
        return self._connect()
        
engine = None

#持有数据库链接的上下文对象
class _DbCtx(threading.local):
    def __init__(self):
        self.connection = None
        self.transactions = 0
        
    def is_init(self):
        return not self.connection is None
    
    def init(self):
        self.connectio = _LasyConnection()
        self.transactions = 0
        
    def cleanup(self):
        self.connection.cleanup()
        self.connection = None
        
    def cursor(self):
        return self.connection.cursor()
        
_db_ctx = _DbCtx



#实现自动获取和释放连接＃
class _ConnectionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True
        return self


    def __exit__(self,exectype,excvalue,traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()


def connection():
    return _ConnectionCtx()


##例子：
##with connection():
######do_some_db_operation()

#更简单的写法是写个@decorator:
#@with_connection
#def do_some_db_operation():
    #pass
#例子：
#@wit_connection
#####def select(sql,*args):
###### pass

