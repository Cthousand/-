import asyncio # 用于定义协程函数和建立事件循环,协程函数只有被注入到事件循环中才能执行,注入之前先要封装成task对象,每一个对象在循环中遇到了阻塞,都会去执行其他的任务
import time
import aiohttp # 导入请求库
import logging # 日志
from motor.motor_asyncio import AsyncIOMotorClient  # 异步mongodb存储

logging.basicConfig(level=logging.INFO,  # 日志配置
                    format='%(asctime)s - %(levelname)s: %(message)s')

index_url = 'https://spa1.scrape.center/api/movie/?limit=10&offset={offset}' # 列表页
detail_url = 'https://spa1.scrape.center/api/movie/{id}' # 详情页
page_number = 10    # 页总数

mongo_db_name = 'movies' # 数据库配置
mongo_collection_name= 'test_movies_aiohttp'
collection= AsyncIOMotorClient('localhost',27017)[mongo_db_name][mongo_collection_name] 

headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}

loop = asyncio.get_event_loop() # 建立事件循环
semaphore = asyncio.Semaphore(10)  # 最大并发数限制
session = aiohttp.ClientSession() # 建立会话实例

async def Common_r_json(url):       # 通用请求方法
    async with semaphore:         # 声明最大并发数
        async with session.get(url,headers=headers) as response: #with as能够声明一个上下文管理下,做到自动分配和释放资源
            await asyncio.sleep(1) # 请求间隔,防止IP封锁
            logging.info('scrap url:%s',url) # 日志记录请求url
            return await response.json()

async def Index_r_json(page):    # 列表页请求>解析
    url = index_url.format(offset=10 * (page - 1))
    json=await Common_r_json(url) 
    return await Index_p_dict(json)

async def Index_p_dict(json):   # 列表页解析
    ids = []
    for item in json.get('results'):
        ids.append(item.get('id'))
    return ids

async def Detail_r_json(id):   # 详情页请求>解析>存储
    url = detail_url.format(id=id)
    json = await Common_r_json(url)
    data_dict=await Detail_p_dict(json)
    return await Save_data(data_dict)

async def Detail_p_dict(json): # 详情页解析
    title=json['name']
    rating_num=json['score']
    brif=json['drama']
    data_dict={'title':title,
        'rating_num':rating_num,
        'brif':brif}
    logging.info('get data %s', data_dict)
    return data_dict

async def Save_data(dict): # 数据保存
    return await collection.update_one({'title': dict.get('title')}, {'$set': dict}, upsert=True) 

async def main(): # 方法调度
    # index tasks 列表页请求异步
    index_tasks = [asyncio.ensure_future(Index_r_json(page)) for page in range(1, page_number+1)] #ensure_future方法用于构造task对象,此处采用了列表生成式
    results= await asyncio.gather(*index_tasks) # gather方法保证了所有任务都都结束才返回结果
    ids=[]
    for i in results: # 结果是一个二维列表,因为需要逐一提取出来
        for j in i:
            ids.append(j)
    # detail tasks 详情页请求+存储异步
    detail_tasks = [asyncio.ensure_future(Detail_r_json(id)) for id in ids] #列表生成式+future方法构造task对象列表
    await asyncio.gather(*detail_tasks) 
    await session.close() # 所有任务结束后不在维持会话


if __name__ == '__main__':
    start=time.time()
    loop.run_until_complete(main()) # 运行该事件循环
    during_time=time.time()-start
    logging.info('over,time_consuming:%s',during_time) # 测试结果:55s,受网速的影响,该值为参考值.