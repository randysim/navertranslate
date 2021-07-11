import requests
import re
import os
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import cv2
import translate
import locate
import math

debugUrl = "https://m.comic.naver.com/webtoon/detail?titleId=756137&no=17&week=thu&listSortOrder=DESC&listPage=1"
prod = True
scriptPath = "C:/Users/phone/PycharmProjects/navertranslate"

tesseractPath = "C:\\Users\\phone\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseractPath

options = "-l {} --psm {}".format("kor", 3)

def ocr_core(file):
    """
    This function will handle the core OCR processing of images.
    """
    img_ref = cv2.imread(file)
    # Threshold to obtain binary image
    thresh = cv2.threshold(img_ref, 220, 255, cv2.THRESH_BINARY)[1]

    # Create custom kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # Perform closing (dilation followed by erosion)
    close = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    text = pytesseract.image_to_string(close, config=options)  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    return text

def downloadImages(urls, output):
    counter = 1
    images = []

    if not os.path.isdir(scriptPath + "/paneloutput/" + output):
        os.mkdir(scriptPath + "/paneloutput/" + output)

    for url in urls:
        extension = url.split(".")[-1]
        path = scriptPath + "/paneloutput/" + output + "/" + str(counter) + "." + extension
        isFile = os.path.isfile(path)

        if isFile == False:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'
            }
            response = requests.get(url, headers=headers)
            with open(path, 'wb') as handle:
                handle.write(response.content)

        print("DOWNLOADING: " + str(counter) + "/" + str(len(urls)))
        counter += 1
        images.append(path)
    print("Finished Downloading Panels: " + output)
    return images

def main():
    print("PATH: " + scriptPath)
    print("TESSERACT: " + tesseractPath)

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
    images = downloadImages(urls, titleId)

    if not os.path.isdir(scriptPath + "/cvoutput/" + titleId):
        os.mkdir(scriptPath + "/cvoutput/" + titleId)

    html = "<html>\n<head></head><body><ul>"

    counter = 1
    for image in images:
        if os.path.isfile(scriptPath + "/cvoutput/" + titleId + "/" + str(counter) + ".txt"):
            readFile = open(scriptPath + "/cvoutput/" + titleId + "/" + str(counter) + ".txt", "r")
            readText = readFile.read()
            html += "<li><p><img src=\"" + image + "\"></p>" + readText + "</li>"
            counter += 1
            continue

        detected = ocr_core(image)

        try:
            translated = translate.translate_text(detected)
        except:
            counter += 1
            continue

        if (translated[0].startswith("TypeError")):
            print("COULD NOT GET TRANSLATION")
            counter += 1
            continue

        file = open(scriptPath + "/cvoutput/" + titleId + "/" + str(counter) + ".txt", "w", encoding=translated[1])
        file.write(translated[0])
        file.close()

        html += "<li><p><img src=\"" + urls[counter] + "\"></p>" + translated[0] + "</li>"

        print("DETECTED: " + str(counter) + "/" + str(len(images)))
        counter += 1

    html += "</ui></body></html>"

    print("WRITING HTML FILE")

    htmlFile = open(scriptPath + "/index.html", "w")
    htmlFile.write(html)
    htmlFile.close()


main()

