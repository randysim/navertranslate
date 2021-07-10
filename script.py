import requests
import re
import os
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import cv2
import math

debugUrl = "https://m.comic.naver.com/webtoon/detail?titleId=756137&no=17&week=thu&listSortOrder=DESC&listPage=1"
prod = False
scriptPath = "C:/Users/phone/PycharmProjects/navertranslate"

tesseractPath = "C:\\Users\\phone\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = tesseractPath

options = "-l {} --psm {}".format("kor", 3)

def decode(scores, geometry, scoreThresh):
    detections = []
    confidences = []

    ############ CHECK DIMENSIONS AND SHAPES OF geometry AND scores ############
    assert len(scores.shape) == 4, "Incorrect dimensions of scores"
    assert len(geometry.shape) == 4, "Incorrect dimensions of geometry"
    assert scores.shape[0] == 1, "Invalid dimensions of scores"
    assert geometry.shape[0] == 1, "Invalid dimensions of geometry"
    assert scores.shape[1] == 1, "Invalid dimensions of scores"
    assert geometry.shape[1] == 5, "Invalid dimensions of geometry"
    assert scores.shape[2] == geometry.shape[2], "Invalid dimensions of scores and geometry"
    assert scores.shape[3] == geometry.shape[3], "Invalid dimensions of scores and geometry"
    height = scores.shape[2]
    width = scores.shape[3]
    for y in range(0, height):

        # Extract data from scores
        scoresData = scores[0][0][y]
        x0_data = geometry[0][0][y]
        x1_data = geometry[0][1][y]
        x2_data = geometry[0][2][y]
        x3_data = geometry[0][3][y]
        anglesData = geometry[0][4][y]
        for x in range(0, width):
            score = scoresData[x]

            # If score is lower than threshold score, move to next x
            if(score < scoreThresh):
                continue

            # Calculate offset
            offsetX = x * 4.0
            offsetY = y * 4.0
            angle = anglesData[x]

            # Calculate cos and sin of angle
            cosA = math.cos(angle)
            sinA = math.sin(angle)
            h = x0_data[x] + x2_data[x]
            w = x1_data[x] + x3_data[x]

            # Calculate offset
            offset = ([offsetX + cosA * x1_data[x] + sinA * x2_data[x], offsetY - sinA * x1_data[x] + cosA * x2_data[x]])

            # Find points for rectangle
            p1 = (-sinA * h + offset[0], -cosA * h + offset[1])
            p3 = (-cosA * w + offset[0],  sinA * w + offset[1])
            center = (0.5*(p1[0]+p3[0]), 0.5*(p1[1]+p3[1]))
            detections.append((center, (w,h), -1*angle * 180.0 / math.pi))
            confidences.append(float(score))

    # Return detections and confidences
    return [detections, confidences]

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



    confThreshold = 0.5
    nmsThreshold = 0.2

    # put this in loop later lol

    net = cv2.dnn.readNetFromTensorflow("frozen_east_text_detection.pb")
    cvImage = cv2.imread(images[0])
    print(ocr_core(images[0]))
    inputWidth = round(cvImage.shape[1]/32) * 32
    inputHeight = round(cvImage.shape[0]/32) * 32
    cvWidth = cvImage.shape[1]/float(inputWidth)
    cvHeight = cvImage.shape[0]/float(inputHeight)

    blob = cv2.dnn.blobFromImage(cvImage, 1.0, (inputWidth, inputHeight), (123.68, 116.78, 103.94), True, False)
    outputLayers = []
    outputLayers.append("feature_fusion/Conv_7/Sigmoid")
    outputLayers.append("feature_fusion/concat_3")

    net.setInput(blob)
    output = net.forward(outputLayers)
    scores = output[0]
    geometry = output[1]
    [boxes, confidences] = decode(scores, geometry, confThreshold)

    indices = cv2.dnn.NMSBoxesRotated(boxes, confidences, confThreshold, nmsThreshold)

    for i in indices:
        # get 4 corners of the rotated rect
        vertices = cv2.boxPoints(boxes[i[0]])

        # scale the bounding box coordinates based on the respective ratios

        for j in range(4):
            vertices[j][0] *= cvWidth
            vertices[j][1] *= cvHeight
        for j in range(4):
            p1 = (int(vertices[j][0]), int(vertices[j][1]))
            p2 = (int(vertices[(j + 1) % 4][0]), int(vertices[(j + 1) % 4][1]))
            cv2.line(cvImage, p1, p2, (0, 255, 0), 1, cv2.LINE_AA)
            # cv.putText(frame, "{:.3f}".format(confidences[i[0]]), (vertices[0][0], vertices[0][1]), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv.LINE_AA)

    cv2.imwrite(scriptPath + "/cvoutput/" + "test.jpg", cvImage)


    """
    for image in images:
        imageText = ocr_core(image)
        print(imageText)
    """

main()

