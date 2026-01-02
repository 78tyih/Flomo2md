import streamlit as st
import os
import re
import io
import zipfile
from bs4 import BeautifulSoup

# --- 页面配置 ---
st.set_page_config(
    page_title="flomo 2 Any - 优雅的笔记迁移工具",
    page_icon="🍃",
    layout="centered"
)

# --- 自定义 CSS 样式 ---
st.markdown("""
    <style>
    /* 调整大标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2D3436;
        margin-bottom: 0.5rem;
    }
    /* 副标题样式 */
    .sub-title {
        color: #636E72;
        margin-bottom: 2rem;
    }
    /* 卡片容器样式 */
    .stFileUploader {
        border: 2px dashed #00B894;
        border-radius: 12px;
        padding: 1rem;
    }
    /* 按钮美化 */
    .stButton>button {
        width: 100%;
        background-color: #00B894;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #55E6C1;
        border: none;
        color: white;
    }
    /* 打赏区域样式 */
    .donate-section {
        background-color: #F9F9F9;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-top: 4rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 逻辑处理函数 ---
def process_flomo_to_zip(html_file, resource_files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        soup = BeautifulSoup(html_file.read().decode('utf-8'), 'html.parser')
        memos = soup.find_all('div', class_='memo')
        total = len(memos)
        
        image_map = {f.name: f.read() for f in resource_files}
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, memo in enumerate(memos):
            progress_bar.progress((i + 1) / total)
            status_text.caption(f"正在打磨第 {i+1}/{total} 篇笔记...")
            
            time_str = memo.find('div', class_='time').get_text()
            content_div = memo.find('div', class_='content')
            content_html = content_div.decode_contents()
            
            for img_tag in content_div.find_all('img'):
                src = img_tag.get('src', '')
                img_name = os.path.basename(src)
                if img_name in image_map:
                    zip_file.writestr(f"assets/{img_name}", image_map[img_name])
                    content_html = content_html.replace(src, f"assets/{img_name}")

            md_text = content_html.replace('<p>', '').replace('</p>', '\n').replace('<br/>', '\n')
            md_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', md_text)
            md_text = re.sub(r'\[\[(.*?)\]\]', r'[[\1]]', md_text)
            md_text = re.sub(r'<img src="(.*?)"/?>', r'![](\1)', md_text)
            md_text = re.sub(r'<[^>]+>', '', md_text)
            
            file_name = f"memo_{re.sub(r'[^\w]', '_', time_str)}_{i}.md"
            md_content = f"---\ntitle: {time_str}\ndate: {time_str}\nsource: flomo\n---\n\n{md_text.strip()}"
            zip_file.writestr(file_name, md_content)
            
    return zip_buffer.getvalue()

# --- 主界面 ---
st.markdown('<p class="main-title">🍃 flomo 2 Any</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">让碎片灵感重获新生。支持一键导出 Markdown，自动本地化图片。</p>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.image("https://flomoapp.com/static/img/logo.png", width=100)
    st.title("使用指南")
    st.markdown("""
    1. **导出**：在 flomo 网页端导出 HTML。
    2. **上传**：将 `index.html` 和 `resource` 文件夹图片上传。
    3. **迁移**：解压后的文件夹直接拖入 **思源笔记** 或 **飞书**。
    """)
    st.divider()
    st.caption("v2.0 | Designed with ❤️ for Note-takers")

# 上传容器
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        html_upload = st.file_uploader("📂 1. 上传 index.html", type="html")
    with col2:
        img_uploads = st.file_uploader("🖼️ 2. 上传资源图片", accept_multiple_files=True)

st.write("") # 间距

if html_upload:
    if st.button("🚀 开始优雅地转换"):
        resources = img_uploads if img_uploads else []
        zip_data = process_flomo_to_zip(html_upload, resources)
        st.balloons()
        st.success("转换已就绪！")
        st.download_button(
            label="💾 下载转换后的 ZIP 包",
            data=zip_data,
            file_name="flomo_export.zip",
            mime="application/zip"
        )

# --- 打赏区域（仅在成功后显示） ---
if success_trigger:
    st.markdown("""
        <div class="donate-card">
            <h3 style='color: #2D3436;'>☕ 请作者喝杯咖啡</h3>
            <p class="donate-text">看到你的灵感重获新生，我也非常开心。<br>如果这个工具为你节省了时间，欢迎支持！</p>
            <p style='color: #B2BEC3; font-size: 0.75rem; margin-bottom: 1rem;'>本工具为纯前端处理，您的笔记不会上传到任何服务器</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 打赏二维码排列
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        # 微信支付（已替换为你的 Raw 链接）
        st.image("https://raw.githubusercontent.com/78tyih/Flomo2md/main/WechatPay.png", caption="微信支付", use_container_width=True)
    with d_col2:
        # 支付宝支付（请确保你仓库里也有这张图，如果没有，可以先注释掉或上传同名文件）
        st.image("https://raw.githubusercontent.com/78tyih/Flomo2md/main/AlipayPay.png", caption="支付宝支付", use_container_width=True)
