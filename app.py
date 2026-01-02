import streamlit as st
import os
import re
import io
import zipfile
from bs4 import BeautifulSoup

# 设置页面
st.set_page_config(page_title="flomo 迁移助手", page_icon="📦")

def process_flomo_to_zip(html_file, resource_files):
    """
    html_file: 上传的 HTML 文件对象
    resource_files: 上传的图片文件列表
    """
    # 创建内存中的 ZIP
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        soup = BeautifulSoup(html_file.read().decode('utf-8'), 'html.parser')
        memos = soup.find_all('div', class_='memo')
        
        # 1. 建立图片查找表 (文件名 -> 文件内容)
        image_map = {f.name: f.read() for f in resource_files}
        
        for i, memo in enumerate(memos):
            time_str = memo.find('div', class_='time').get_text()
            content_div = memo.find('div', class_='content')
            
            # 处理内容
            content_html = content_div.decode_contents()
            
            # --- 图片本地化核心逻辑 ---
            # 找到所有的 <img> 标签
            for img_tag in content_div.find_all('img'):
                src = img_tag.get('src', '')
                # flomo 图片路径通常是 "resource/123.jpg"
                img_name = os.path.basename(src)
                
                if img_name in image_map:
                    # 将图片写入 ZIP 的 assets 文件夹
                    new_img_path = f"assets/{img_name}"
                    zip_file.writestr(new_img_path, image_map[img_name])
                    # 更新 MD 中的引用为相对路径
                    content_html = content_html.replace(src, new_img_path)

            # --- 格式清洗 ---
            md_text = content_html.replace('<p>', '').replace('</p>', '\n').replace('<br/>', '\n')
            md_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', md_text)
            md_text = re.sub(r'\[\[(.*?)\]\]', r'[[\1]]', md_text)
            # 针对思源/飞书：把 <img> 标签转为 Markdown 语法
            md_text = re.sub(r'<img src="(.*?)"/?>', r'![](\1)', md_text)
            md_text = re.sub(r'<[^>]+>', '', md_text)
            
            # 生成文件名
            safe_time = re.sub(r'[^\w]', '_', time_str)
            file_name = f"memo_{safe_time}_{i}.md"
            
            # 写入 Markdown 到 ZIP
            md_content = f"---\ntitle: {time_str}\ndate: {time_str}\nsource: flomo\n---\n\n{md_text.strip()}"
            zip_file.writestr(file_name, md_content)
            
    return zip_buffer.getvalue()

# --- Streamlit UI ---
st.title("📦 flomo 全能迁移工具")
st.markdown("支持将笔记转换为 Markdown，并自动提取图片到 `assets` 目录，适配思源与飞书。")

with st.sidebar:
    st.header("使用说明")
    st.info("""
    1. 上传 flomo 导出的 `index.html`。
    2. 在下方上传 `resource` 文件夹内的所有图片。
    3. 点击转换并下载 ZIP。
    """)

# 文件上传
html_upload = st.file_uploader("1. 上传 index.html", type="html")
img_uploads = st.file_uploader("2. 上传 resource 文件夹内的所有图片（可多选）", accept_multiple_files=True)

if html_upload and st.button("开始转换"):
    with st.spinner("正在处理笔记和图片..."):
        # 即使没有图片也传个空列表
        resources = img_uploads if img_uploads else []
        zip_data = process_flomo_to_zip(html_upload, resources)
        
        st.success("转换成功！")
        st.download_button(
            label="📥 下载转换后的笔记包 (ZIP)",
            data=zip_data,
            file_name="flomo_export_ready.zip",
            mime="application/zip"
        )