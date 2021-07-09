import requests;

def main():
    comicUrl = input("Naver Webtoon Url: ")
    print("Fetching from: " + comicUrl)

    res = requests.get(comicUrl);
    data = res.json()

    print(data)


main()