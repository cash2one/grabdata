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
import re
from bs4 import BeautifulSoup as BS
import datetime
import threading
lock = threading.Lock()

class Captcha(threading.Thread):
    def __init__(self, captchaUrl,url,beian,threadID, name, captfile='',datafile='',start_num=0,end_num=0):
        threading.Thread.__init__(self)
        self.threadID = threadID  #线程ID
        self.name = name   #线程名称，用于标识
        self.captfile = captfile  #验证码图片文件
        self.datafile = datafile+'.txt'  #验证码识别后生成的txt文件
        self.datafile2 = datafile
        self.captchaUrl = captchaUrl   #验证码生成页
        self.url = url     #备案号和验证码提交页
        self.beian = beian  #备案号名称初始化
        self.start_num = start_num   #起始备案号
        self.end_num = end_num      #终止备案号


    def run(self):
        print("Starting " + self.name)
        t1 = datetime.datetime.now()
        for i in range(self.start_num,self.end_num):
            n = str(i).zfill(6)
            self.beian_full = "%s%d%s%s" % (self.beian, 16, n, '号')  #循环补全备案号，并开始查询
            print('开始查询：', self.beian_full)
            self.driver = webdriver.Chrome('D:\Program files\chromedriver_win32\chromedriver')
            self.getSearch()
        print("Exiting " + self.name)
        print(datetime.datetime.now()-t1)

    def getCaptcha(self):
        self.driver.get(self.captchaUrl)
        time.sleep(1)   #截频前需要等待网页完全加载……
        self.driver.save_screenshot(self.captfile)
        captchaValue = self.readCaptcha(self.captfile)
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
        cv2.imwrite(self.captfile, th2)
        p = subprocess.Popen(
            ["C:/Program Files (x86)/Tesseract-OCR/tesseract.exe",self.captfile, self.datafile2, '-l', 'normal'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)                         #文件生成需要隔片刻才能读取到。
        f = open(self.datafile, "r")
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
            # time.sleep(1)  # 测试完毕，可去掉。
            elem2 = self.driver.find_element_by_id('z3')
            elem2.send_keys(self.beian_full)
            # time.sleep(1)
            # 填写验证码
            text = captchaValue
            print('验证码为：' + text)
            elem1 = self.driver.find_element_by_id('textfield7')
            elem1.send_keys(text)

            # 提交表单
            elem3 = self.driver.find_element_by_id('button1')
            elem3.send_keys(Keys.RETURN)
            page = self.driver.page_source

            soup = BS(page,'lxml')
            if soup.select('.by')[0].string == '详细信息':  #查询成功！
                if soup.select('#1') == []:
                    print('查询成功！没有符合条件的记录')
                    # print(soup)
                else:
                    print('查询成功！入库成功')
                    lock.acquire()
                    try:
                        f = open('ICP备案data/北京备案数据4.txt', 'r+')
                        f.read()
                        html = soup.select('#1')
                        a = BS(str(html[0]), 'lxml')
                        data = []
                        for string in a.stripped_strings:
                            data.append(repr(string))
                        f.write('\n' + str(data))
                        f.close()
                    finally:
                        lock.release()



            else:
                return self.getSearch()

        finally:
            self.driver.quit()

# City = ['京','沪','浙','苏', '津','冀', '晋', '蒙', '辽', '吉', '黑', '皖', '闽', '赣', '鲁', '豫', '鄂',
#             '湘', '粤','桂', '琼', '渝', '蜀', '黔', '滇', '陇', '藏', '陕', '青', '宁', '新']
beian = '京ICP备'
captchaUrl = 'http://www.miitbeian.gov.cn/getVerifyCode'
url = 'http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_showPage.action'
list = []
for i in range(2,4):
    list.append(i)
adict = locals()
for i,s in enumerate(list):
    adict['thread%s' % (i+1)] = Captcha(captchaUrl, url, beian, s, "Thread-"+str(s), 'captcha'+str(s)+'.jpg', 'captcha'+str(s), 2750+(s-1)*10+1, 2750+s*10+1)
    adict['thread%s' % (i + 1)].start()
# thread1 = Captcha(captchaUrl, url, beian, 1, "Thread-1", 'captcha1.jpg', 'captcha1',998,1000)
# thread2 = Captcha(captchaUrl, url, beian, 2, "Thread-2", 'captcha2.jpg', 'captcha2',1473,1501)
# thread3 = Captcha(captchaUrl, url, beian, 3, "Thread-3", 'captcha3.jpg', 'captcha3',1591,1601)
#
#
# thread1.start()
# thread2.start()
# thread3.start()
print("Exiting Main Thread")



