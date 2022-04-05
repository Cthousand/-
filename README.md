# 四种方式爬取同一网站的速度差异

## 1. 四种方式

[requests,aiohttp,selenium,pyppeteer],这四种方法的主要区分点:

1. requests和aiohttp属于抓包,selenium和pyppeteer属于js渲染提取.抓包会更快一点,因为抓包省去了浏览器页面渲染的过程.

2. requsts和selenium属于同步,aiohttp和pyppeteer属于异步.异步会更快一点,异步和同步这2种方式,打个比方同步就像是一个人必要要烧完水才能够打少卫生,而异步就像是先让水烧着,但这时候去打扫卫生,等水烧好了,再切换回来,所以后者能够更多的运行人的性能.

所以理论上,这四种方式的排名顺序是:

aiohttp>requests>pyppeteer>selenium

## 2. 最终结果

aiohttp>requests>selenium>pyppeteer

| 方式      | 耗时/s |
| --------- | ------ |
| aiohttp   | 56     |
| requests  | 130    |
| selenium  | 179    |
| pyppeteer | 200    |

## 3. 测试方法

url:https://spa1.scrape.center/

<img src="/Users/qc/Library/Application Support/typora-user-images/image-20220406010105630.png" alt="image-20220406010105630" style="zoom: 33%;" />

点击第一个

<img src="/Users/qc/Library/Application Support/typora-user-images/image-20220406010232442.png" alt="image-20220406010232442" style="zoom: 33%;" />

要保存的数据就是每一部电影的标题,评分和简介这三块内容

大体思路如下:

![image-20220406010909110](/Users/qc/Library/Application Support/typora-user-images/image-20220406010909110.png)

## 4. 实践过程遇到的障碍

1. aiohttp方法中,

   ```python
   collection= AsyncIOMotorClient('mongodb://localhost:27017')[mongo_db_name][mongo_collection_name] 
   ```

   报错:显示port应为int之类,如何解决?

   解决方法:查阅官方文档,好像要用这种方式传递

   <img src="/Users/qc/Library/Application Support/typora-user-images/image-20220406013306059.png" alt="image-20220406013306059" style="zoom:50%;" />

   于是改成了:

   ```python
   collection= AsyncIOMotorClient('localhost',27017)[mongo_db_name][mongo_collection_name] 
   ```

   果然解决了问题.

2. 在pyppeteer方法中,自带的chromium浏览器一打开显示缺少api什么的,总是崩溃,如何解决?

   解决方法:`browser = await launch(filename='userdata',executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=False,args=['--disable-infobars']) `

   在参数executablePath传递进你的chrome浏览器执行文件窗口

   官方文档网址:https://pyppeteer.github.io/pyppeteer/reference.html#launcher

   <img src="/Users/qc/Library/Application Support/typora-user-images/image-20220406015241099.png" alt="image-20220406015241099" style="zoom: 50%;" />

   

3. 在pyppeteer方法中,采用querySelectorallEval方法选取并提取节点文本时,css选择器对于某些节点不如xpath方便,如何绕过这个方法?

<img src="/Users/qc/Library/Application Support/typora-user-images/image-20220406020128547.png" alt="image-20220406020128547" style="zoom:50%;" />

这里采用xpath选择器,注意其返回的是一个列表,然后用evaluate方法传入js语言提取.

```python
urls_node=await tab.Jx('//h2[@class="m-b-sm"]/parent::*') # xpath选择,返回的是一个列表
urls=[]
for url_node in urls_node:
  url = await tab.evaluate('node => node.href', url_node) # js语言提取链接,此处返回的是全链接,无需拼接,挺特别的
  urls.append(url)
  return urls
```

理论上,返回的应该是上图中标红的,实测返回的是全链接(不知道有没有大佬能解释一下?)

## 5. 感言

事实上,我在实践的过程中遇到的困难其实并不止这些,但最终只能记住印象深刻的,对于已经理解消化的障碍仿佛遗忘了它们,后面可能对针对多线程和多进程再做一个项目练习,比较这两种方式在速度上的差异.这是我的第一篇项目复盘,希望能开个好头,坚持下去,用输出倒逼输入,做到真正的理解消化.

