import streamlit as st
import os
import re
import io
import zipfile
from bs4 import BeautifulSoup

# 设置页面
st.set_page_config(page_title="flomo 迁移助手", page_icon="📦")

def process_flomo_to_zip(html_file, resource_files):
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        soup = BeautifulSoup(html_file.read().decode('utf-8'), 'html.parser')
        memos = soup.find_all('div', class_='memo')
        total_memos = len(memos)
        
        # 1. 建立图片查找表
        image_map = {f.name: f.read() for f in resource_files}
        
        # 2. 创建进度条占位符
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, memo in enumerate(memos):
            # 更新进度条
            percent_complete = (i + 1) / total_memos
            progress_bar.progress(percent_complete)
            status_text.text(f"正在处理第 {i+1}/{total_memos} 条笔记...")
            
            time_str = memo.find('div', class_='time').get_text()
            content_div = memo.find('div', class_='content')
            content_html = content_div.decode_contents()
            
            # 图片处理
            for img_tag in content_div.find_all('img'):
                src = img_tag.get('src', '')
                img_name = os.path.basename(src)
                if img_name in image_map:
                    new_img_path = f"assets/{img_name}"
                    zip_file.writestr(new_img_path, image_map[img_name])
                    content_html = content_html.replace(src, new_img_path)

            # 格式清洗
            md_text = content_html.replace('<p>', '').replace('</p>', '\n').replace('<br/>', '\n')
            md_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', md_text)
            md_text = re.sub(r'\[\[(.*?)\]\]', r'[[\1]]', md_text)
            md_text = re.sub(r'<img src="(.*?)"/?>', r'![](\1)', md_text)
            md_text = re.sub(r'<[^>]+>', '', md_text)
            
            file_name = f"memo_{re.sub(r'[^\w]', '_', time_str)}_{i}.md"
            md_content = f"---\ntitle: {time_str}\ndate: {time_str}\nsource: flomo\n---\n\n{md_text.strip()}"
            zip_file.writestr(file_name, md_content)
            
        status_text.text("✅ 所有笔记处理完成！正在生成压缩包...")
            
    return zip_buffer.getvalue()

# --- Streamlit UI ---
st.title("📦 flomo 全能迁移工具")

# 产品经理建议：增加醒目的风险提示和引导
st.info("💡 **温馨提示**：若您的笔记中图片较多，上传过程可能较慢。上传完成后点击转换，请耐心等待进度条走完。")

with st.sidebar:
    st.header("使用说明")
    st.write("1. 上传 flomo 导出的 `index.html`。")
    st.write("2. 全选并上传 `resource` 文件夹内的图片。")
    st.write("3. 点击下方按钮，系统将自动打包图片至 `assets` 目录并修正链接。")

html_upload = st.file_uploader("1. 上传 index.html", type="html")
img_uploads = st.file_uploader("2. 上传 resource 文件夹内的图片（可多选）", accept_multiple_files=True)

if html_upload:
    if st.button("🚀 开始转换并打包"):
        resources = img_uploads if img_uploads else []
        zip_data = process_flomo_to_zip(html_upload, resources)
        
        st.balloons() # 成功的仪式感：撒花
        st.download_button(
            label="📥 点击下载转换后的笔记包 (ZIP)",
            data=zip_data,
            file_name="flomo_export_ready.zip",
            mime="application/zip"
        )
