import time
from selenium import webdriver # 用于构建浏览器实例
from selenium.webdriver.common.by import By # 方法选择
from selenium.webdriver.support import expected_conditions as EC  # 异常情况
from selenium.webdriver.support.wait import WebDriverWait # 显式等待
import logging # 日志
from urllib.parse import urljoin # 合并url
import pymongo # 存储库

logging.basicConfig(level=logging.INFO, # 日志配置
                    format='%(asctime)s - %(levelname)s: %(message)s')

index_url = 'https://spa1.scrape.center/page/{page}' # 列表页
detail_url='https://spa1.scrape.center'  # 详情页
timeout = 10 # 显式等待最长时间
total_page = 10 # 页码数

mongo_name = 'movies' # 数据库配置
mongo_collection_name = 'selenium_movies'
collection= pymongo.MongoClient('localhost',27017)[mongo_name][mongo_collection_name]

options = webdriver.ChromeOptions() # 实例化浏览器参数配置
options.add_experimental_option('excludeSwitches', ['enable-automation']) # 隐藏提示条和去掉开发者警告
options.add_experimental_option('useAutomationExtension', False)  
# options.add_argument('--headless') # 开启无头模式

browser = webdriver.Chrome(options=options)  # 建立浏览器实例,并导入配置
wait = WebDriverWait(browser,timeout) # 设置显示等待,指定最长等待时间


def Common_r(url, condition, locator): #通用请求方法,conditon用于传递等待结束需要的条件,locator执行等待对象
    logging.info('scraping %s', url) # 记录初始请求信息
    browser.get(url)
    wait.until(condition(locator)) # 等待直到制定条件出现
 
def Index_r(page):   # 列表页请求
    url = index_url.format(page=page)
    Common_r(url, condition=EC.visibility_of_all_elements_located, # 传递url,条件,位置到请求API中,条件是所有指定元素成功加载完成
                locator=(By.XPATH, '//*[@id="index"]//h2[@class="m-b-sm"]/parent::a')) # 该位置为列表中电影的名称

def Index_p_gens(): # 列表页解析
    elements = browser.find_elements_by_xpath('//*[@id="index"]//h2[@class="m-b-sm"]/parent::a') # 找到母节点
    for element in elements:
        href = element.get_attribute('href') # 找到url链接
        yield urljoin(detail_url, href)  # 拼接并传递url

def Detail_r(url): # 详情页请求
    Common_r(url, condition=EC.visibility_of_element_located,  # 传递url,条件,位置到请求api中
                locator=(By.XPATH, '//div[contains(@class,"item")]')) 

def Detail_p_dict(): # 详情页解析
    title = browser.find_element_by_css_selector('.m-b-sm').text
    score = browser.find_element_by_xpath('//p[contains(@class,"score")]').text
    brif = browser.find_element_by_xpath('//h3/following-sibling::p').text
    data={
        'title': title,
        'score': score,
        'brif': brif
    }
    logging.info('get data:%s',data)
    return data

def Data_save(data): # 保存数据
    collection.update_one({'title':data.get('title')},{'$set':data},upsert=True)

def main(): # 方法调度
    try:
        for page in range(1, total_page + 1):
            Index_r(page)
            detail_urls = Index_p_gens()
            for detail_url in list(detail_urls): # 此处注意要将生成器对象转化成list对象,否则会运行失败,具体原因还不清楚
                Detail_r(detail_url)
                data=Detail_p_dict()
                Data_save(data)
    finally:
        browser.close()


if __name__ == '__main__':
    start=time.time()
    main()
    during_time=time.time()-start
    logging.info('over,time comsuming:%s',during_time) # 测试结果:总计耗时:190s

