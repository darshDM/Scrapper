# Libraries
import multiprocessing
from bs4 import BeautifulSoup
import requests
import bs4
import datetime
import urllib.request
import pandas as pd
import pytesseract
from pytesseract import image_to_string 
from PIL import Image, ImageOps, ImageEnhance
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import cv2 
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
from CaptchaRecognition import get_string
from multiprocessing import Process


# get captcha text from screenshot
def get_captcha_text(location, size,state):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    im = Image.open("D:/Internship/My scrapper/{part}.png".format(part=state)) # uses PIL library to open image in memory
    left = location['x'] + 115
    top = location['y'] + 72
    right = location['x'] + size['width'] + 82
    bottom = location['y'] + size['height'] + 65


    im = im.crop((left, top, right, bottom)) # defines crop points
    im.save("D:/Internship/My scrapper/{part}.png".format(part=state))
    im = cv2.imread("D:/Internship/My scrapper/{part}.png".format(part=state))
    
    cv2.imwrite("D:/Internship/My scrapper/{part}.png".format(part=state),im)
    captcha_text = get_string("D:/Internship/My scrapper/{part}.png".format(part=state))
    return captcha_text

# download pdf from url
def pdfdownload(url,filename,cookie):
    
    # Add cookie for authenticating the request
    requestsJar = requests.cookies.RequestsCookieJar()
    requestsJar.set("PHPSESSID",cookie)
    
    response = requests.get(url,cookies=requestsJar)
    
    # create pdf file and dump the data from url
    file = open("D:/Internship/pdffiles/PdfDocument Scarping2/" + filename + ".pdf", 'wb')
    file.write(response.content)
    file.close()

def login_to_website(state,FromDate,ToDate,url,sema):
    sema.acquire()
    driver = webdriver.Chrome(executable_path = "D:/Internship/chromedriver.exe")
    driver.get(url)
    
    # find part of the page you want image of
    element = driver.find_element_by_id('captcha_image') 
    location = element.location
    size = element.size
    driver.save_screenshot('D:/Internship/My scrapper/{part}.png'.format(part=state))
    
    #storing cookies for furthur downloads
    cookies = driver.get_cookies()
    driver.find_element_by_id("to_date").send_keys(ToDate)
    driver.find_element_by_id("from_date").send_keys(FromDate)
    captcha = driver.find_element_by_id('captcha_image')
    
    # get captcha text
    captcha_text = get_captcha_text(location, size,state)
    captcha.send_keys(captcha_text)
    print(captcha_text)
    driver.find_element_by_id("captcha").send_keys(captcha_text)
    sleep(5)
    
    #clicking the button
    driver.find_element_by_xpath("/html/body/form/div[2]/div[4]/span[3]/input[1]").click()    
    
    sleep(5)
    try_again = False
    inValid = driver.find_element_by_id("txtmsg").get_attribute("title")
    print(len(captcha_text),inValid)
    if(inValid == "Invalid Captcha"):
        try_again = True

    else:
        page_source = driver.page_source
        soup1 = BeautifulSoup(page_source, 'lxml')
        type(soup1)
        bs4.BeautifulSoup
        title = soup1.title
        case=[]
        CaseType_CaseNumber_CaseYear=[]
        Order_Date=[]
        Order_Number=[]
        status=[]
        
        # getting table of all pdfs
        PDF_file_Table_tag=soup1.find("tbody",{"id":"showList1"})

        tr_tag=PDF_file_Table_tag.find_all("tr")
        for i in range(len(tr_tag)):
            td_tag=tr_tag[i].find_all("td") [0] 
            td_tag1=tr_tag[i].find_all("td")[1]
            td_tag2=tr_tag[i].find_all("td")[2]
            td_tag3=tr_tag[i].find_all("td")[3]
            

            case.append(td_tag.text)
            CaseType_CaseNumber_CaseYear.append(td_tag1.text)
            Order_Date.append(td_tag2.text)
            Order_Number.append(td_tag3.text)
            
            
            document=td_tag1.text
            print(document,state,sep=":")
            try:
                # try going into link
                a_tag_url=td_tag3.find("a")["href"]
                status.append(a_tag_url)
                # download each file
                pdfdownload("https://services.ecourts.gov.in/ecourtindiaHC/cases/"+ a_tag_url,document.replace("/"," "),cookies[0]["value"])

                
            except:
                Order_Number.append("NaN")
                print("No Document")
                
        a={"case":case,"CaseType_CaseNumber_CaseYear":CaseType_CaseNumber_CaseYear,"Order_Date":Order_Date,"Order_Number":Order_Number,"statulink":status}
                
        df = pd.DataFrame.from_dict(a, orient='index')
        df = df.transpose()
        
        # store details of each case in CSV file
        df.to_csv(r"D:\Internship\pdffiles\csvfiles\courtt.csv", sep=',',index=False)
        df.head(50)

    if try_again == True:
        login_to_website(state,FromDate,ToDate,url)   
    driver.close()
    sema.release()

    
def allStates():
    driver = webdriver.Chrome(executable_path = "D:/Internship/chromedriver.exe")
    driver.get("https://services.ecourts.gov.in/ecourtindiaHC/")
    
    # getting list of all the states with one court
    stateList = driver.find_elements_by_xpath("/html/body/div/ul/li/a")
    stateLinks = list()
    stateName = list()
    for state in stateList:
        stateName.append(state.text)
        stateLinks.append(state.get_attribute("href"))
    
    # getting list of all the states with multiple court
    stateList = driver.find_elements_by_xpath("/html/body/div/ul/li/ul/li/a")
    for state in stateList:
        stateName.append(state.text)
        stateLinks.append(state.get_attribute("href"))
    
    byDate = list()
    
    # creating list of links for cases by date for each court
    for link in stateLinks:
        driver.get(link)
        try:
            item = driver.find_element_by_xpath("/html/body/div[3]/ul/li[2]/ol/li[5]/a")
        except:
            item = driver.find_element_by_xpath("/html/body/div/ul/li[2]/ol/li[5]/a")
        byDate.append(item.get_attribute("href"))
    
    # visit each court site and get all the cases for current date
    current_date = datetime.datetime.now()

    sema = multiprocessing.Semaphore(multiprocessing.cpu_count()-1)
    login_to_website(stateName[0],current_date.strftime("%d-%m-%Y"),current_date.strftime("%d-%m-%Y"),byDate[0],sema)

    # Multiprocessing
    # processes = []
    # sema = multiprocessing.Semaphore(multiprocessing.cpu_count()-1)
    # for i in range(len(byDate)):
    #     p = Process(target=login_to_website,args=(stateName[i],"30-6-2021","30-6-2021",byDate[i],sema))
    #     processes.append(p)
    #     p.start()

    # for p in processes:
    #     p.join()
    

if __name__ == '__main__':
    allStates()
    