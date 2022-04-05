import asyncio
import json
import time
import aiohttp
import logging
from motor.motor_asyncio import AsyncIOMotorClient  # 异步mongodb存储

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

index_url = 'https://spa1.scrape.center/api/movie/?limit=10&offset={offset}'
detail_url = 'https://spa1.scrape.center/api/movie/{id}'
page_size = 10      # 每页列表数量
page_number = 10    # 页总数

mongo_db_name = 'movies' # 数据库配置
mongo_collection_name= 'test_movies_aiohttp'
collection= AsyncIOMotorClient('localhost',27017)[mongo_db_name][mongo_collection_name] 

loop = asyncio.get_event_loop() # 建立事件循环
headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
semaphore = asyncio.Semaphore(10)  # 最大并发数限制
session = aiohttp.ClientSession() # 建立会话实例

async def Common_r_json(url):       # 通用请求方法,返回json对象
    async with semaphore:         # 声明最大并发数
        async with session.get(url,headers=headers) as response:
            await asyncio.sleep(1) # 请求间隔,防止封锁ip
            logging.info('scrap url:%s',url) # 日志记录请求url
            return await response.json()

async def Index_r_json(page):    # 列表页请求>解析
    url = index_url.format(offset=page_size * (page - 1))
    json=await Common_r_json(url) 
    # print(json)
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
    index_tasks = [asyncio.ensure_future(Index_r_json(page)) for page in range(1, page_number+1)]
    results= await asyncio.gather(*index_tasks)
    ids=[]
    for i in results:
        for j in i:
            ids.append(j)
    # detail tasks 详情页请求+存储异步
    detail_tasks = [asyncio.ensure_future(Detail_r_json(id)) for id in ids]
    await asyncio.gather(*detail_tasks)
    await session.close()


if __name__ == '__main__':
    start=time.time()
    loop.run_until_complete(main())
    during_time=time.time()-start
    logging.info('over,time_consuming:%s',during_time)
