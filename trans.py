from googletrans import Translator
from mysqldbClass import db
from multiprocessing import Pool
import threading
from concurrent.futures import ThreadPoolExecutor
import os

# 获取分类
def get_product():
    # sql = "SELECT id, `name` FROM product where (category_id between 2 and 21) and (trans_name = '')"
    sql = "SELECT id, `name` FROM product where trans_name = '' order by id asc"

    try:
        # 执行SQL语句
        return db.ExecQuery(sql)
    except:
        print("Error: unable to fetch data")

def update_trans(id, productName):
    transName = productName.replace("\\'", "'").replace("'", "\\'").replace("，", ",")
    sql = "UPDATE product SET trans_name = '" + transName +"' WHERE id = " + str(id)
    try:
        # 执行SQL语句
        return db.ExecNonQuery(sql)
    except Exception as e:
        print(e)
        print("Error: unable to update, productName:" +productName+ ", transName:" + transName +", sql:" + sql)

def begin_trans(translator, id, productName):
    # print('%s:%s is running' % (threading.currentThread().getName(), os.getpid()))
    transName = (translator.translate(productName.replace("\\'", "'").replace("'", "\\'"), src='id', dest='zh-CN').text)
    print("productOriginName: " + productName + ",  translateName:" + transName)
    update_trans(id, transName)
if __name__=='__main__':
    print('Parent process %s.' % os.getpid())
    p = Pool(10)
    translator = Translator()
    for result in get_product():
        productId = result[0]
        productName = result[1]
        msg = p.apply_async(begin_trans, args=(translator, productId, productName,))
        print(msg)
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')


# if __name__ == '__main__':
#     # 参数默认是CPU个数*5
#     p = ThreadPoolExecutor(max_workers=4)
#
#     print('Parent process %s.' % os.getpid())
#     translator = Translator()
#     for result in get_product():
#         productId = result[0]
#         productName = result[1]
#         msg = p.submit(begin_trans, translator, productId, productName)
#         print(msg)
#     print('Waiting for all subprocesses done...')
#     p.shutdown()  # 等同于p.close(),p.join()
#     print('All subprocesses done.')