import urllib.request
import urllib.parse
import sys
import json



if __name__ == "__main__":
    
    word=sys.argv[1]

    url="https://fanyi.baidu.com/sug"

    headers={
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    }

    data={
        
    }

    data["kw"]=word

    data=urllib.parse.urlencode(data).encode('utf-8')


    request=urllib.request.Request(url=url,data=data,headers=headers)


    response=urllib.request.urlopen(request)

    content=response.read().decode('utf-8')

    obj=json.loads(content)

    result=obj['data']

    for translate in result:
        resultone=translate['v']
        fromone=translate['k']
        output=f"{fromone}->{resultone}"
        print(output)
        