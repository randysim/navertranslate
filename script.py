import requests
import re
import os
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

debugUrl = "https://m.comic.naver.com/webtoon/detail?titleId=756137&no=17&week=thu&listSortOrder=DESC&listPage=1"
prod = False
scriptPath = "C:/Users/phone/PycharmProjects/navertranslate"

tesseractPath = "C:\\Users\\phone\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseractPath

options = "-l {} --psm {}".format("kor", 3)


def ocr_core(filename):
    """
    This function will handle the core OCR processing of images.
    """
    text = pytesseract.image_to_string(Image.open(filename), config=options)  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    return text

def downloadImages(urls, output):
    counter = 1
    images = []

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
    imageText = ocr_core(images[0])
    print(images[0])
    print(imageText)

    """
    for image in images:
        imageText = ocr_core(image)
        print(imageText)
    """

main()

