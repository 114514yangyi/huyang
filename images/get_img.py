import requests
import os

# 创建保存目录

for i in range(100):
    try:
        # 获取随机图片URL
        response = requests.get(
            "https://www.dmoe.cc/random.php?return=json", timeout=10
        )
        response.raise_for_status()  # 检查HTTP状态码

        data = response.json()
        img_url = data["imgurl"]

        print(f"正在下载第 {i + 1}/100 张图片: {img_url}")

        # 下载图片
        img_response = requests.get(img_url, timeout=30)
        img_response.raise_for_status()

        # 提取文件名
        filename = f"image_{i + 1:03d}.jpg"

        # 保存图片
        with open(filename, "wb") as f:
            f.write(img_response.content)

        print(f"✓ 保存成功: {filename}")

    except requests.exceptions.RequestException as e:
        print(f"✗ 网络错误: {e}")
    except KeyError:
        print("✗ JSON数据中缺少 'imgurl' 字段")
    except Exception as e:
        print(f"✗ 未知错误: {e}")
