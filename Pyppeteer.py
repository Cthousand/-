import logging
import asyncio
from pyppeteer import launch # 类似于selenium中webdriver
import time
from motor.motor_asyncio import AsyncIOMotorClient  # 异步mongodb存储

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

loop=asyncio.get_event_loop()  # 建立事件循环

mongo_db_name = 'movies' # 数据库配置
mongo_collection_name= 'pyppeteer_test_movies'
collection= AsyncIOMotorClient('localhost',27017)[mongo_db_name][mongo_collection_name] # 此处要遵守api规定

index_url = 'https://spa1.scrape.center/page/{page}' # 列表页
detail_url='https://spa1.scrape.center' # 详情页
timeout = 10 # 超时时间
total_page = 10 # 总页数

browser, tab = None, None # 声明变量,为了不在每一个方法中都配置一次,在init函数中声明全局


async def Init():   # 配置浏览器,此处没有用内置的的chromium(本机测试不稳定),此外对于携程对象或方法均要➕await修饰
    global browser, tab
    browser = await launch(filename='userdata',executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=False,
                           args=['--disable-infobars'])  # 指定了用户目录,这样就不用每次都加载cookie了,--disable-infobars隐藏提示条,但实测下来没有用,可能是因为指定了浏览器?
    tab = await browser.newPage()  # 新建浏览器页面

async def Common_r(url, selector): # 通用请求方法
    logging.info('scraping %s', url) # 记录请求信息
    await tab.goto(url) # 请求页面
    await tab.waitForSelector(selector, options={   # 设置条件超时:等待直到指定元素出现后或超出10s
            'timeout': timeout * 1000
        })

async def Index_r(page): # 列表页请求
    url = index_url.format(page=page)
    await Common_r(url, '.m-b-sm') #以名称出现为条件等待

async def Index_p_url():  # 列表页解析
    urls_node=await tab.Jx('//h2[@class="m-b-sm"]/parent::*') # xpath选择,返回的是一个列表
    urls=[]
    for url_node in urls_node:
        url = await tab.evaluate('node => node.href', url_node) # js语言提取,此处返回的是全链接,无需拼接,挺特别的
        urls.append(url)
    return urls

async def Detail_r(url): # 详情页请求
    await Common_r(url, '.drama') # 以简介出现为条件

async def Detail_p_dict(): # 详情页解析
    title = await tab.querySelectorEval('.m-b-sm','node=>node.innerText') # 提取标题
    score = await tab.querySelectorEval('.score','node=>node.innerText')  # 提起评分
    brif = await tab.querySelectorEval('.drama p','node=>node.innerText') # 提取简介
    data={
        'title': title,
        'score': score,
        'brif': brif
    }
    logging.info('get data:%s',data) # 记录保存的数据
    return data

def Data_save(data): # 保存数据
    collection.update_one({'title':data.get('title')},{'$set':data},upsert=True) # 存在则更新,不存在则插入

async def main(): # 方法调度
    await Init()  # 启动浏览器和新建页面
    try:
        for page in range(1, total_page+ 1): # 页码遍历
            await Index_r(page) # 列表请求
            detail_urls = await Index_p_url() # 列表解析
            for detail_url in detail_urls: # 详情页url遍历
                await Detail_r(detail_url) # 详情页请求
                detail_data = await Detail_p_dict() # 详情页解析
                Data_save(detail_data) #数据保存
    finally:
        await browser.close()  # 无论有没有运行成功,都关闭浏览器


if __name__ == '__main__':
    start=time.time()
    loop.run_until_complete(main()) # 启动事件循环
    during_time=time.time()-start
    logging.info('over time consuming:%s',during_time) # 测试耗时: