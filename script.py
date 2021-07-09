import requests
import re

debugUrl = "https://m.comic.naver.com/webtoon/detail?titleId=756137&no=17&week=thu&listSortOrder=DESC&listPage=1"
prod = False

def main():
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

        urls.append(listComp[firstQuote:secondQuote])

    print(urls)


main()