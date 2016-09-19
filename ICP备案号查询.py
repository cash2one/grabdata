from urllib import request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import cv2
import numpy as np
import subprocess
from matplotlib import pyplot as plt
from xlrd import open_workbook
import re
from bs4 import BeautifulSoup as BS
import datetime

###读取验证码文件，并识别返回文本

#创建一个用于读取sheet的生成器,依次生成每行数据,row_count 用于指定读取多少行, col_count 指定用于读取多少列

class Captcha(object):
    def __init__(self, captchaUrl,url,beian):
        self.captchaUrl = captchaUrl
        self.url = url
        self.beian = beian
        self.driver = webdriver.PhantomJS(executable_path="phantomjs.exe")
        # self.driver = webdriver.Chrome('D:\Program files\chromedriver_win32\chromedriver')
    def getCaptcha(self):
        self.driver.get(self.captchaUrl)
        # time.sleep(1)
        self.driver.render('example.png')
        # self.driver.render('captcha.jpg')
        self.driver.save_screenshot('captcha.jpg')
        captchaValue = self.readCaptcha('example.png')
        print(captchaValue)
        if len(captchaValue) == 6:
            pattern = re.compile(r'[0-9a-zA-Z]{6}')
            match = pattern.match(captchaValue)
            if match:
                print('验证码格式终于正确啦')
                return captchaValue
            else:
                print('验证码错误，请重新识别')
                return self.getCaptcha()
        else:
            print('验证码格式错误，请重新识别')
            return self.getCaptcha()

    def readCaptcha(self,file):
        img = cv2.imread(file)
        cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
        blur = cv2.blur(img, (4, 4))
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)  # 灰度化
        ret, thresh = cv2.threshold(gray, 127, 255, 0)  # 二值化
        kernel = np.ones((4, 4), np.uint8)
        erosion = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        gaosi = cv2.GaussianBlur(erosion, (3, 3), 0)
        ret, th2 = cv2.threshold(gaosi, 127, 255, 0)
        cv2.imwrite('captcha.jpg', th2)
        p = subprocess.Popen(
            ["C:/Program Files (x86)/Tesseract-OCR/tesseract.exe", 'captcha.jpg', "captcha", '-l', 'normal'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)
        f = open("captcha.txt", "r")
        # Clean any whitespace characters
        captchaValue = f.read().replace(" ", "").replace("\n", "")
        return captchaValue

    def getSearch(self):
        captchaValue = self.getCaptcha()
        self.driver.get(self.url)
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "button1"))
            )
            # 公司名称
            inputs = self.driver.find_elements_by_tag_name('input')
            for input in inputs:
                if input.get_attribute('id') == 'z3':
                    input.click()
            time.sleep(1)  # 测试完毕，可去掉。
            elem2 = self.driver.find_element_by_id('z3')
            elem2.send_keys(self.beian)
            time.sleep(1)
            # 填写验证码
            text = captchaValue
            print('验证码为：' + text)
            elem1 = self.driver.find_element_by_id('textfield7')
            elem1.send_keys(text)

            # 提交表单
            elem3 = self.driver.find_element_by_id('button1')
            elem3.send_keys(Keys.RETURN)
            # self.driver.find_elements_by_name('unitName')
            # try:
            #     self.driver.find_element_by_id('1')
            #     print(2222)
            #     print(self.driver.page_source)
            # except:
            #     print(3333)
            #     return self.getSearch()
            page = self.driver.page_source

            soup = BS(page,'lxml')
            if soup.select('.by')[0].string == '详细信息':  #查询成功！
                if soup.select('#1') == []:
                    print('查询成功！没有符合条件的记录')
                else:
                    print('查询成功！入库成功')
                    f.read()
                    html = soup.select('#1')
                    a =BS(str(html[0]),'lxml')
                    data = []
                    for string in a.stripped_strings:
                        data.append(repr(string))
                    f.write('\n' + str(data))

            else:
                return self.getSearch()

        finally:
            self.driver.quit()

def readsheet(s, row_count=-1, col_count=-1):#
    # Sheet 有多少行
    nrows = s.nrows
    # Sheet 有多少列
    ncols = s.ncols
    row_count = (row_count if row_count > 0 else nrows)
    col_count = (col_count if col_count > 0 else ncols)
    row_index = 0
    while row_index < row_count:
        yield [s.cell(row_index, col).value for col in range(col_count)]
        row_index += 1


captchaUrl = 'http://www.miitbeian.gov.cn/getVerifyCode'
url = 'http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_showPage.action'
# City = ['京','沪','浙','苏', '津','冀', '晋', '蒙', '辽', '吉', '黑', '皖', '闽', '赣', '鲁', '豫', '鄂',
#             '湘', '粤','桂', '琼', '渝', '蜀', '黔', '滇', '陇', '藏', '陕', '青', '宁', '新']
City = ['京']
f = open('ICP备案data/北京备案数据4.txt', 'r+')
d1 = datetime.datetime.now()
for city in City:
    beian0 = "%s%s" % (city,'ICP备')
    for i in range(3451, 3461):   #首先遍历采集35000条备案数据。每500条一组，分组采集。
        n = str(i).zfill(6)
        beian = "%s%d%s%s" % (beian0,16,n,'号')
        print('开始查询：',beian)
        capt = Captcha(captchaUrl, url, beian)
        capt.getSearch()
        # try:
        #     capt.getSearch()
        # except:
        #     print('error!')
        #     break
f.close()
d2 = datetime.datetime.now()
print(d2-d1)