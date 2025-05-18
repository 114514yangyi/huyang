import urllib.request
import urllib.parse
import json
import sys


def begin_grab(start:int):

    limit=20

    url="https://movie.douban.com/j/chart/top_list?type=5&interval_id=100%3A90&action="
    url+=f"&start={start}&limit={limit}"


    headers={
        "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    }

    request=urllib.request.Request(url=url,headers=headers)

    response=urllib.request.urlopen(request)

    content=response.read().decode('utf-8')

    list_=json.loads(content)


        

    with open("down.txt","a" ,encoding='utf-8') as fp:
        
        for index in range(1,len(list_)):
            name=list_[index]['title']
            fp.write(f"{index+start}.<<{name}>>\n")
        
        
if __name__ == '__main__' :
    parameters=sys.argv
    if(len(parameters)==1):
        start=int(input("输入需要获取的电影组数。(20为一组)"))
    else :
        start=int(parameters[1])
    with open("down.txt","w") as fp:
        fp.truncate(0)
        
    for page in range(0,start*20+1,20):
        begin_grab(page)
else:
    begin_grab(1)
        


