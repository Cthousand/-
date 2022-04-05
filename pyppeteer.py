import logging
import asyncio
from pyppeteer import launch
import time
from motor.motor_asyncio import AsyncIOMotorClient
from sympy import det  # 异步mongodb存储

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

mongo_db_name = 'movies' # 数据库配置
mongo_collection_name= 'pyppeteer_test_movies'
collection= AsyncIOMotorClient('localhost',27017)[mongo_db_name][mongo_collection_name] 

index_url = 'https://spa1.scrape.center/page/{page}'
detail_url='https://spa1.scrape.center'
timeout = 10
total_page = 10
browser, tab = None, None
headless = False  # 设置有头模式


async def Init():   # 新建浏览器指定用户目录和chrome浏览器,此次需要用async+await 调用launch方法
    global browser, tab
    browser = await launch(filename='userdata',executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=headless,
                           args=['--disable-infobars']) 
    tab = await browser.newPage()  

async def Common_r(url, selector): # 通用请求方法
    logging.info('scraping %s', url) # 记录请求信息
    await tab.goto(url) 
    await tab.waitForSelector(selector, options={   # 设置条件超时
            'timeout': timeout * 1000
        })

async def Index_r(page): # 列表页请求
    url = index_url.format(page=page)
    await Common_r(url, '.m-b-sm') #以名称出现为条件等待

async def Index_p_url():  # 列表页解析
    urls_node=await tab.Jx('//h2[@class="m-b-sm"]/parent::*') # xpath选择,返回的是一个列表
    urls=[]
    for url_node in urls_node:
        url = await tab.evaluate('node => node.href', url_node) # js语言提取链接,此处返回的是全链接,无需拼接,挺特别的
        urls.append(url)
    return urls

async def Detail_r(url): # 详情页请求
    await Common_r(url, '.drama') # 以简介出现为条件

async def Detail_p_dict(): # 详情页解析
    title = await tab.querySelectorEval('.m-b-sm','node=>node.innerText')
    score = await tab.querySelectorEval('.score','node=>node.innerText')
    brif = await tab.querySelectorEval('.drama p','node=>node.innerText')
    data={
        'title': title,
        'score': score,
        'brif': brif
    }
    logging.info('get data:%s',data)
    return data

def Data_save(data): # 保存数据
    collection.update_one({'title':data.get('title')},{'$set':data},upsert=True) # 存在则更新,不存在则插入

async def main(): # 方法调度
    await Init() 
    try:
        for page in range(1, total_page+ 1): # 页码遍历
            await Index_r(page) # 列表请求
            detail_urls = await Index_p_url() # 列表解析
            for detail_url in detail_urls: # 详情页url遍历
                await Detail_r(detail_url) # 详情页请求
                detail_data = await Detail_p_dict() # 详情页解析
                Data_save(detail_data) #数据保存
    finally:
        await browser.close()


if __name__ == '__main__':
    start=time.time()
    asyncio.get_event_loop().run_until_complete(main())
    during_time=time.time()-start
    logging.info('over time consuming:%s',during_time)
