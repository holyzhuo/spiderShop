import platform
from selenium import webdriver
from mysqldbClass import db
from multiprocessing import Pool
import os


def get_driver():
    # chromeoption参数设置
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    # 根据不同环境区分driver
    env = platform.system()
    if env == 'Windows':  # windows
        chromePath = 'E:\zcer\code\chromedriver_win32/chromedriver.exe'
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
    elif env == 'Darwin':  # mac
        chromePath = '/usr/local/var/www/python/chromedriver'
    else:  # linux
        chromePath = '/usr/bin/chromedriver'
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')

    try:
        driver = webdriver.Chrome(chromePath, chrome_options=chrome_options)
    except Exception as e:
        print(e)
    finally:
        return driver


# 获取分类
def get_category():
    sql = "SELECT id, `name` ,url FROM category where id in (22, 29, 49, 55)" # 需修改部分

    try:
        return db.ExecQuery(sql)  # 执行SQL语句
    except:
        print("Error: unable to fetch data")


# 爬取单个商品数据
def spider_data(categoryId, categoryUrl):
    print('Run task %s (%s)...' % (str(categoryId), os.getpid()))
    sortList = {'1': '8', '2': '5'} # 根据销量排序和根据评分排序
    driver = get_driver()
    for key, value in sortList.items():
        currentCount = 0
        limitCount = 200
        page = 1

        hrefList = []

        while currentCount < limitCount:
            print(categoryUrl + "?ob=" + value + "&page=" + str(page))
            finalUrl = categoryUrl + "?ob=" + value + "&page=" + str(page)
            driver.get(finalUrl)

            productHeadEndDivs = driver.find_elements_by_class_name('ta-slot-card')
            headDivs = productHeadEndDivs[0:len(productHeadEndDivs) - 1]
            endDivs = productHeadEndDivs[len(productHeadEndDivs) - 1:]
            productMiddleDivs = driver.find_elements_by_class_name('category-product-box')

            onePageNum = len(productHeadEndDivs) + len(productMiddleDivs)
            if onePageNum != 60 and onePageNum != 48:
                print('good not enough url:' + finalUrl)
                continue
            print(len(productHeadEndDivs), len(productMiddleDivs), onePageNum)
            if onePageNum == 0:
                break

            for div in headDivs:
                items = div.find_elements_by_tag_name("a")
                if len(hrefList) < limitCount:
                    hrefList.append(items[1].get_attribute('href'))

            for div in productMiddleDivs:
                items = div.find_elements_by_tag_name("a")
                if len(hrefList) < limitCount:
                    hrefList.append(items[1].get_attribute('href'))

            for div in endDivs:
                items = div.find_elements_by_tag_name("a")
                if len(hrefList) < limitCount:
                    hrefList.append(items[1].get_attribute('href'))

            page += 1
            currentCount += onePageNum

        print(len(hrefList), hrefList)
        for item in hrefList:
            isSuccess = 0
            tryCount = 1  # 单个产品最大重试获取次数(有可能出现产品不存在404的情况)
            while not isSuccess and tryCount < 10:
                try:
                    driver.get(item)
                    salesCount = driver.find_element_by_class_name('all-transaction-count').text.replace(' ', '')
                    salesCount = salesCount if salesCount != '' else '0'
                    productName = driver.find_element_by_class_name('rvm-product-title').text.replace("'", "\\'")
                    imageUrl = driver.find_element_by_class_name('content-main-img').find_element_by_tag_name(
                        'img').get_attribute(
                        'src')
                    shopName = driver.find_element_by_id('shop-name-info').text.replace("'", "\\'")
                    productSalePrice = driver.find_element_by_class_name('rvm-price').find_elements_by_tag_name('span')[
                        -1].get_attribute('content')
                    productOriginPrice = driver.find_element_by_class_name('rvm-price--old').text[3:].replace('.', '')
                    productOriginPrice = productOriginPrice if productOriginPrice != '' else '0'
                    successRate = driver.find_element_by_class_name('success-transaction-percent').text
                    isSuccess = 1
                except Exception as e:
                    print('category id: ' + str(categoryId) + ' ,retry count:' + str(tryCount) + ', Error:', e)
                    tryCount += 1
                    driver.quit()
                    driver = get_driver()
                    continue

                # SQL 插入语句
                if isSuccess:
                    sql = "INSERT INTO product(category_id, product_url, image_url, `name`, shop_name, original_price, price, sales, txn_success_rate, `type`)" \
                          " VALUES ('" + str(categoryId) + "', '" + str(item) + "', '" + str(imageUrl) + "', '" + str(
                        productName) + "' , '" + str(shopName) + "', '" + str(productOriginPrice) + "', '" + \
                          str(productSalePrice) + "','" + str(salesCount) + "', '" + str(successRate) + "', '" + str(
                        key) + "')"

                    try:
                        print(sql)
                        db.ExecNonQuery(sql)  # 执行sql语句
                    except Exception as e:
                        print("error:" + str(e))
    driver.quit()


if __name__ == '__main__':
    print('Parent process %s.' % os.getpid())
    p = Pool(4)
    for result in get_category():
        categoryId = result[0]
        categoryUrl = result[2]
        p.apply_async(spider_data, args=(categoryId, categoryUrl,))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')
