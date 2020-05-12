#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql

class DbClient(object):
    """
    数据库操作类
    """
    # db实例集
    instances = {}

    def __new__(cls, *args, **kwargs):
        """
        实例化方法
        :arg args
        :arg kwargs
        :return db实例
        """
        _key = "_".join([str(s) for s in args[0].values()])
        if _key not in DbClient.instances:
            DbClient.instances[_key] = super(DbClient, cls).__new__(cls)
        return DbClient.instances[_key]


    def __init__(self, _conf):
        """
        构造函数（连接数据库)
        :arg ret_type mysql数据返回格式，默认数组
        """
        self.host = _conf.get('host', '127.0.0.1')
        self.port = int(_conf.get('port', 3306))
        self.user = _conf.get('user', 'root')
        self.passwd = _conf.get('passwd', '')
        self.dbname = _conf.get('dbname', 'mysql')
        self.charset = _conf.get('charset', 'utf8')
        self.rettype = _conf.get('rettype', 'dict')
        # 初始化链接
        self.db_connect()


    def db_connect(self):
        """
        数据库链接
        """
        try:
            self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, \
                                        password=self.passwd, database=self.dbname, charset=self.charset)
            self.conn.autocommit(True)

            if self.rettype == 'dict':
                self.cursor_type = pymysql.cursors.DictCursor
            else:
                self.cursor_type = pymysql.cursors.Cursor
            self.cursor = self.conn.cursor(cursor=self.cursor_type)
        except pymysql.Error as e:
            print ("Mysql Connect Error: {}".format(e))
        except Exception as e:
            print ("Mysql Connect Exception: {}".format(e))


    def insert(self, table, params):
        """
        插入数据
        :arg table 数据表
        :arg params 插入参数集
        :return 操作结果
        """
        if isinstance(params, dict) is False:
            return self.insert_obj(table, params)

        properties = ','.join(pymysql.escape_string(s) for s in params.keys())
        values = [pymysql.escape_string(str(s)) for s in params.values()]
        value_str = ','.join(['%s' for i in range(len(params))])
        str_sql = 'insert into {} ({}) values({})'.format(table, properties, value_str)
        result = self.execute(str_sql, values)
        return result


    def insert_obj(self, table, obj):
        """
        插入数据
        :arg table 数据表
        :arg obj 插入对象
        :return 操作结果
        """
        return self.insert(table, obj.__dict__)


    # def batch_insert(self, table, params):
    #     """
    #     批量插入数据
    #     :arg table:数据表
    #     :arg params：要插入的参数
    #     return:error/1
    #     """
    #     TODO


    def update(self, table, conds, params):
        """
        更新数据
        :arg table 数据表
        :arg conds 更新条件集
        :arg params 更新数据集
        :return 数字(正常) None(异常)
        """
        if isinstance(params, dict) is False:
            return self.update_obj(table, conds, params)

        conds = self.validateConds(conds)
        if conds is None:
            return None

        setValue = ','.join(["{}=%s".format(k) for k in params.keys()])
        values = [pymysql.escape_string(str(s)) for s in params.values()]
        str_sql = 'update {} set {} where {}'.format(table, setValue, conds)
        result = self.execute(str_sql, values)
        return result


    def update_obj(self, table, conds, obj):
        """
        更新记录
        :arg table 数据表
        :arg conds 条件集
        :arg obj 数据对象
        :return 数字(正常) None(异常)
        """
        return self.update(table, conds, obj.__dict__)


    def query(self, sql):
        """
        指定sql查询
        :arg sql sql语句
        :return 数据集
        """
        result = self.execute(sql)
        if result is None:
            return None
        ret = self.cursor.fetchall()
        return ret


    def select(self, table, columns='*', conds='1=1', offset=0, limit=10000):
        """
        查询数据表某条件下的部分数据
        :arg table 数据表
        :arg columns 检索字段集
        :arg conds 检索条件集
        :arg offset 偏移量
        :arg limit 查询数量
        :return 数据集(正常) None(异常)
        """
        conds = self.validateConds(conds)
        if conds is None:
            return None

        str_sql = 'select {} from {} where {} limit {} offset {}'.format(columns, table, conds, limit, offset)
        result = self.execute(str_sql)
        if result is None:
            return None
        ret = self.cursor.fetchall()
        return ret


    def select_count(self, table, conds='1=1'):
        """
        查询某条件下数据条数
        :arg table:数据表
        :arg conds:条件
        :return 数字(正常) None(异常)
        """
        count = 0
        ret = self.select(table, 'count(*)', conds)
        if ret is None:
            return None

        if self.cursor_type == pymysql.cursors.Cursor:
            count = int(ret[0][0])
        else:
            count = int(ret[0]['count(*)'])
        return count


    def delete(self, table, conds):
        """
        删除数据表数据
        :arg table 数据表
        :arg conds 操作条件集
        :return 数字(正常) None(异常)
        """
        conds = self.validateConds(conds)
        if conds is None:
            return None

        str_sql = 'delete from {} where {}'.format(table, conds)
        result = self.execute(str_sql)
        return result


    def execute(self, sql, args=None):
        """
        数据库执行操作(单sql查询建议使用query方法)
        :arg sql 待执行sql
        :arg args 预处理数据集
        :return 数据集/数字(正常) None(异常）
        """
        try:
            ret = self.cursor.execute(sql, args)
            print ("sql: {}, args: {}".format(sql, args))
            return ret
        except (pymysql.Error, AttributeError) as e:
            err_msg = "{}".format(e)
            print ("Mysql Error: {}, SQL: {}".format(err_msg, sql))
            if ('MySQL server has gone away' in err_msg) or ('Lost connection to MySQL' in err_msg):
                self.db_connect()
                return self.cursor.execute(sql, args)
        except Exception as e:
            print ("Mysql Exception: {}".format(e))
        return None


    def close(self):
        """
        关闭数据库实例
        :arg
        :return
        """
        self.cursor.close()
        self.conn.close()


    def validateConds(self, conds):
        """
        校验conds合法性并转换
        :arg params 查询条件集
        :return 检索条件字符串(正常) None(异常)
        """
        if isinstance(conds, dict):
            cond_list = []
            for _k, _v in conds.items():
                cond_list.append("{}='{}'".format(pymysql.escape_string(str(_k)), pymysql.escape_string(str(_v))))
            conds = ' and '.join(cond_list)
        elif isinstance(conds, str) is False:
            conds = None
        else:
            pass
        return conds


    def validateColumns(self, columns):
        """
        校验columns合法性并转换
        :arg columns 查询字段集
        :return 检索字段字符串(正常) None(异常)
        """
        if isinstance(columns, list):
            columns = ','.join(columns)
        elif isinstance(columns, str) is False:
            columns = None
        else:
            pass
        return columns
