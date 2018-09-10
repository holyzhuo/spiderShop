import requests
# url = 'https://www.tokopedia.com/jualbonekamurah/boneka-beruang-teddy-bear-jumbo-besar-pink?src=topads'
# headers = {'user-agent': 'my-app/0.0.1'}
# response = requests.get(url, headers=headers)
# print(response.text)

from selenium import webdriver
import time
import pymysql
from mysqldbClass import db

# 获取分类
def get_category():
    sql = "SELECT id, `name` ,url FROM category"

    try:
        # 执行SQL语句
        return db.ExecQuery(sql)
    except:
        print("Error: unable to fetch data")

for result in get_category():
    categoryId = result[0]
    categoryName = result[1]
    categoryUrl = result[2]

    sortList = { '1':'8', '2':'5' }
    for key,value in sortList.items():
        currentCount = 0
        limitCount = 200
        page = 1
        chromePath = 'E:\zcer\code\chromedriver_win32/chromedriver.exe'
        # chromePath = '/usr/local/var/www/python/chromedriver' # mac
        driver = webdriver.Chrome(chromePath)
        hrefList = []

        while currentCount < limitCount:
            print(categoryUrl + "?ob="+value+"&page=" + str(page))
            driver.get(categoryUrl + "?ob="+value+"&page=" + str(page))

            productHeadEndDivs = driver.find_elements_by_class_name('ta-slot-card')
            headDivs = productHeadEndDivs[0:len(productHeadEndDivs) - 1]
            endDivs = productHeadEndDivs[len(productHeadEndDivs) - 1:]
            productMiddleDivs = driver.find_elements_by_class_name('category-product-box')

            onePageNum = len(productHeadEndDivs) + len(productMiddleDivs)
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

            time.sleep(1)

        print(len(hrefList), hrefList)
        for item in hrefList:
            driver.get(item)

            try:
                salesCount = driver.find_element_by_class_name('all-transaction-count').text.replace(' ', '')
                salesCount = salesCount if  salesCount != '' else '0'
                productName = driver.find_element_by_class_name('rvm-product-title').text.replace("'", "\\'")
                imageUrl = driver.find_element_by_class_name('content-main-img').find_element_by_tag_name(
                    'img').get_attribute(
                    'src')
                shopName = driver.find_element_by_id('shop-name-info').text.replace("'", "\\'")
                productSalePrice = driver.find_element_by_class_name('rvm-price').find_elements_by_tag_name('span')[
                    -1].get_attribute('content')
                productOriginPrice = driver.find_element_by_class_name('rvm-price--old').text[3:].replace('.', '')
                productOriginPrice = productOriginPrice if  productOriginPrice != '' else '0'
                successRate = driver.find_element_by_class_name('success-transaction-percent').text
                isSuccess = 1
            except:
                isSuccess = 0

            # SQL 插入语句
            if isSuccess:
                sql = "INSERT INTO product(category_id, product_url, image_url, `name`, shop_name, original_price, price, sales, txn_success_rate, `type`)" \
                      " VALUES ('" + str(categoryId) + "', '" + str(item) + "', '"+ str(imageUrl) + "', '"+str(productName)+"' , '" + str(shopName)+"', '"+str(productOriginPrice)+"', '"+\
                      str(productSalePrice)+"',"+str(salesCount)+", '"+str(successRate)+"', '"+str(key)+"')"
            else:
                sql = "INSERT INTO product(category_id, product_url, success) VALUES ('" + str(categoryId) + "','"+str(item)+"','"+str(isSuccess)+"')"

            try:
                # 执行sql语句
                print(sql)
                db.ExecNonQuery(sql)
                # 提交到数据库执行
            except:
                # 如果发生错误则回滚
                print("error")

        driver.quit()

#
# print(salesCount, productName, imageUrl, shopName, productSalePrice, productOriginPrice)
# time.sleep(1)
# driver.quit()

