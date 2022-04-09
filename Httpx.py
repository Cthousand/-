from httplib2 import RedirectLimit
import httpx # 请求 和requests类似,但支持http2.0协议,但开启需要事先声明,此外该库也支持异步
import time 
import logging # 日志
import pymongo # 存储
from urllib.parse import urljoin # 合并url

logging_filename='request_douban_movies_logging.txt'  # 日志配置
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s-%(levelname)s:%(message)s')

url='https://spa1.scrape.center/api/movie/?limit=10&offset={offset}'       # 列表页url
detail_url_root='https://spa1.scrape.center/api/movie/{id}'            # 详情页url

total_page=10 # 总页数

headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'} #请求头

mongo_connect_name='mongodb://localhost:27017' #mongodb存储配置
mongo_db_name='movies'
mongo_collection_name='httpx_movies'
collection=pymongo.MongoClient(mongo_connect_name)[mongo_db_name][mongo_collection_name]

seq=1 #数据长度参数


def Common_json(url):  #通用请求方法
    with httpx.Client() as client: # 默认的表示http1.1 如写成http2=True表示开启
        r=client.get(url,headers=headers,follow_redirects=True) # 没有follow_redirects 显示301报错,网页被永久移除,猜测是不支持默认重定向,查官方文档,果然..
        logging.info('scrap url:%s',url) # 日志记录请求url
        return r.json()

def Index_jsons(page): #列表页请求
    index_url=url.format(offset=(page-1)*10)
    return Common_json(index_url)

def Detail_urls(json): #列表页解析
    for i in range(len(json['results'])):
            detail_url_id=json['results'][i]['id']
            yield urljoin(detail_url_root,str(detail_url_id)) # 合并时注意将ID转化成字符串

def Detail_html(url): #详情页请求
    return Common_json(url)

def Detail_data(json): #详情页解析
    global seq  # 此处是为了查看数据条数, 校验有无遗漏部分
    try: 
        title=json['name']
        rating_num=json['score']
        brif=json['drama']
        data={'title':title,
                'rating_num':rating_num,
                'brif':brif}
        logging.info(f'get data:{seq}:{data}')
        seq+=1
        return data
    except:
        logging.error('Detail_data:%s 解析失败!',json,exc_info=True)

def Data_save(data): #数据保存
    collection.update_one({'name':data.get('name')},{'$set':data},upsert=True) # upsert为True表示存在则替换,不存在则插入

def main(): #方法调度
    for page in range(1,total_page+1): # 两层展开的第一层,页数
        index_html=Index_jsons(page) # 拿到列表页的json文本
        detail_urls=Detail_urls(index_html) #从json文本中提取详情页的url
        for detail_url in detail_urls: # 两层展开的第二次,每一页的条目
            detail_html=Detail_html(detail_url) # 拿到详情页中的json文本
            print(detail_html)
            detail_data=Detail_data(detail_html) # 从json文本中提取所需的数据
            Data_save(detail_data) # 存储数据
 
if __name__=='__main__':  # __name__是每个脚步内置的变量,__main__代表当前模块的名称,此处限定了只有在当前脚本下执行,如为import导入则不执行.
    start=time.time()
    main()
    during_time=time.time()-start
    logging.info('over,time_consuming:%s',during_time) # 测试结果:开启了运行重定向,结果导向了很多其他域名的网站,怎么避免这种情况呢?
# 与requests类似,猜测开了异步应该和aiohttp类似,那这样岂不是只要学httpx库一种就可以了?









    


