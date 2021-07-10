import requests
import re
import cv2
import os
import urllib.request

debugUrl = "https://m.comic.naver.com/webtoon/detail?titleId=756137&no=17&week=thu&listSortOrder=DESC&listPage=1"
prod = False
scriptPath = "C:/Users/phone/PycharmProjects/navertranslate"

def downloadImages(urls, output):
    counter = 1

    for url in urls:
        extension = url.split(".")[-1]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'
        }
        response = requests.get(url, headers=headers)
        with open(scriptPath + "/paneloutput/" + output + "/" + str(counter) + "." + extension, 'wb') as handle:
            handle.write(response.content)

        print("DOWNLOADING: " + str(counter) + "/" + str(len(urls)))
        counter += 1
    print("Finished Downloading Panels: " + output)

def main():
    print("PATH: " + scriptPath)

    comicUrl = debugUrl

    if prod:
        comicUrl = input("Naver Webtoon Url: ")

    print("Fetching from: " + comicUrl)

    data = requests.get(comicUrl).text
    cutOne = data.find("<ul>")
    cutTwo = data.find("</ul>")

    listComp = data[cutOne + 4:cutTwo]
    dataIndexes = [m.start() for m in re.finditer("data-src", listComp)]
    urls = []

    for index in dataIndexes:
        firstQuote = listComp.find('"', index)
        secondQuote = listComp.find('"', firstQuote+1)

        urls.append(listComp[firstQuote + 1:secondQuote])

    titleId = comicUrl[comicUrl.find("titleId=") + 8 : comicUrl.find("&")]
    print("Title ID: " + titleId)
    downloadImages(urls, titleId)

main()

