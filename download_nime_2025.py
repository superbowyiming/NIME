import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 配置区 ---
# 1. 设置下载年份
TARGET_YEAR = 2025

# 2. 设置保存到的盘符或文件夹
#    - 直接存到E盘
#    - 存到E盘的某个文件夹: "E:\\NIME_Downloads"
SAVE_BASE_PATH = "E:\\" 
# --- 配置区结束 ---


# 论文主页和网站根地址
PAPERS_URL = "https://nime.org/papers/"
BASE_URL = "https://nime.org/"

def download_nime_papers():
    """
    访问NIME论文主页，下载指定年份的所有PDF论文。
    """
    # 构造最终的保存文件夹路径
    save_dir_name = f"NIME_{TARGET_YEAR}_Papers"
    final_save_dir = os.path.join(SAVE_BASE_PATH, save_dir_name)

    # 1. 创建本地保存文件夹
    try:
        if not os.path.exists(final_save_dir):
            os.makedirs(final_save_dir)
            print(f"成功创建文件夹: {final_save_dir}")
        else:
            print(f"文件夹已存在: {final_save_dir}")
    except OSError as e:
        print(f"错误：无法创建文件夹 {final_save_dir}。")
        print(f"请检查路径 '{SAVE_BASE_PATH}' 是否存在且有写入权限。错误信息: {e}")
        return

    # 2. 访问唯一的论文列表页面
    try:
        print(f"正在访问论文主页: {PAPERS_URL}")
        response = requests.get(PAPERS_URL, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"网络连接或请求错误: {e}")
        return

    # 3. 使用BeautifulSoup解析HTML并筛选链接
    soup = BeautifulSoup(response.text, 'html.parser')
    
    pdf_links = []
    # 查找所有<a>标签
    for link in soup.find_all('a', href=True):
        href = link['href']
        # 关键筛选逻辑：
        # 1. 链接路径中必须包含年份，格式为 "/2025/"
        # 2. 链接必须以 ".pdf" 结尾
        if f"/{TARGET_YEAR}/" in href and href.lower().endswith('.pdf'):
            # 将相对链接 (如 /proceedings/2024/paper.pdf) 转换为绝对链接
            full_pdf_url = urljoin(BASE_URL, href)
            if full_pdf_url not in pdf_links: # 避免重复链接
                pdf_links.append(full_pdf_url)

    # 4. 检查是否找到论文
    if not pdf_links:
        print(f"\n在主页上未找到任何 {TARGET_YEAR} 年的论文。")
        print("这很可能是因为该年份的论文尚未发布。请在论文发布后再运行此脚本。")
        return

    print(f"\n成功找到 {len(pdf_links)} 篇 {TARGET_YEAR} 年的论文。准备开始下载...")

    # 5. 循环下载所有找到的PDF文件
    for i, pdf_url in enumerate(pdf_links):
        # 从URL中提取文件名
        filename = os.path.basename(pdf_url)
        save_path = os.path.join(final_save_dir, filename)

        # 检查文件是否已存在，实现断点续传
        if os.path.exists(save_path):
            print(f"({i+1}/{len(pdf_links)}) 文件已存在，跳过: {filename}")
            continue

        try:
            print(f"({i+1}/{len(pdf_links)}) 正在下载: {filename} ...")
            pdf_response = requests.get(pdf_url, stream=True, timeout=60)
            pdf_response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  -> 下载完成: {filename}")

        except requests.exceptions.RequestException as e:
            print(f"  -> 下载失败: {filename}, 错误: {e}")
            if os.path.exists(save_path):
                os.remove(save_path) # 删除下载不完整的文件

    print(f"\n所有 {TARGET_YEAR} 年的下载任务已完成！文件保存在: {final_save_dir}")

if __name__ == "__main__":
    download_nime_papers()
