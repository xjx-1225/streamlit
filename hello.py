import streamlit as st
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from collections import Counter
import string
import re
from pyecharts.charts import WordCloud
import plotly.graph_objects as go
import plotly.graph_objs as go

def get_web_content(url):
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"获取网页内容时发生错误: {e}")
        return None

# 获取网页正文
def get_webpage_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    return text

def analyze_web_content(web_content):
    if web_content is not None:
        soup = BeautifulSoup(web_content, 'html.parser')
        text_content = soup.get_text()

        # 移除文本中的标点符号和单个字母或数字
        translator = str.maketrans('', '', string.punctuation)
        text_content = text_content.translate(translator)

        words = text_content.split()
        # 过滤掉单个字母或数字
        words = [word for word in words if len(word) > 1]
        word_counter = Counter(words)
        return word_counter

def plot_word_cloud(web_content):
    words = list(web_content.keys())
    values = list(web_content.values())

    c = (
        PyechartsWordCloud()
        .add("", list(zip(words, values)), word_size_range=[20, 100])
        .set_global_opts(title_opts=opts.TitleOpts(title="词云"))
        .render("wordcloud.html")
    )

    st.components.v1.html(open("wordcloud.html", "r", encoding="utf-8").read(), height=500)


def plot_chart(counter, title, chart_type):
    # 获取排名前20的词语（不包括标点符号）
    filtered_counter = {word: count for word, count in counter.items() if word.isalnum()}
    top_words = dict(sorted(filtered_counter.items(), key=lambda x: x[1], reverse=True)[:20])

    labels, values = zip(*top_words.items())

    data = {'labels': labels, 'values': values}

    # 初始化fig
    fig = px.scatter(data, x='labels', y='values')  # 指定数据

    if chart_type == '柱状图':
        fig = px.bar(data, x='labels', y='values', labels={'values': '数量'}, title=title)
        plt.xticks(rotation=45, ha="right")
    elif chart_type == '饼图':
        fig = px.pie(data, names='labels', values='values', title=title, hole=0.3)
    elif chart_type == '折线图':
        fig = px.line(data, x='labels', y='values', labels={'values': '数量'}, title=title, markers=True)
        plt.xticks(rotation=45, ha="right")
    elif chart_type == '瀑布图':
        # 创建瀑布图
        fig = go.Figure(go.Waterfall(
            name="",
            orientation="v",
            measure=["relative"] * len(values),
            x=labels,
            textposition="outside",
            text=values,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        plt.xticks(rotation=45, ha="right")
    elif chart_type == '词云图':
        wordcloud = (
            WordCloud()
            .add(series_name="词云图", data_pair=top_words.items(), word_size_range=[20, 100])
            .set_global_opts(  # 请根据你使用的库进行相应的修改
                title_opts={'text': title},
                tooltip_opts={'is_show': True},
            )
        )
        wordcloud.render("wordcloud.html")  # 将词云图保存为html文件
        st.components.v1.html(open("wordcloud.html", "r", encoding="utf-8").read(), width=1000, height=6000)
        fig.update_layout(title=title, showlegend=False)
        # 添加悬停信息
        fig.update_traces(hovertemplate='词语: %{x}<br>数量: %{y}')
        fig.update_layout(xaxis=dict(tickangle=45))
    elif chart_type == '散点图':
        fig = px.scatter(data, x='labels', y='values', labels={'values': '数量'}, title=title)
        plt.xticks(rotation=45, ha="right")
    elif chart_type == '雷达图':
        fig = go.Figure()

        # 添加雷达图的轴和数据
        fig.add_trace(go.Scatterpolar(
            r=data['values'],
            theta=data['labels'],
            fill='toself',
            name='雷达图'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(data['values'])]  # 适当调整雷达图的轴范围
                )),
            showlegend=False,
            title=title
        )

    # 显示图表
    st.plotly_chart(fig)


def main():
    st.set_page_config(page_title="网页词语分析", page_icon="📊", layout="wide")

    st.title("网页词语分析")

    url = st.text_input("输入网页URL:")

    # 获取用户选择的图表类型
    # 将图表类型选项放入sidebar
    with st.sidebar:
        chart_type = st.radio("选择图表类型:", ["柱状图", "饼图", "折线图", "瀑布图","词云图","散点图","雷达图"])

    if url:
        web_content = get_web_content(url)
        if web_content:
            word_counter = analyze_web_content(web_content)

            webpage_content = get_webpage_text(url)

            # 显示网页内容
            if webpage_content is not None:
                st.text_area("网页内容", value=webpage_content, height=150)
                st.text("排名前20的词频统计结果：")
                # 分析词频
                word_counter = analyze_web_content(webpage_content)
                # 显示排名前20的词频统计结果
                for idx, (word, freq) in enumerate(word_counter.most_common(20), 1):
                    st.write(f"{idx}. {word}: {freq}")
            # 获取排名前20的词语（不包括标点符号）
            filtered_counter = {word: count for word, count in word_counter.items() if word.isalnum()}
            top_words = dict(sorted(filtered_counter.items(), key=lambda x: x[1], reverse=True)[:20])
            # 补充后面词频最高的词语
            remaining_words = dict(sorted(word_counter.items(), key=lambda x: x[1], reverse=True)[20:])
            # 合并前20和后面词频最高的词语
            final_words = {**top_words, **remaining_words}
            # 根据用户选择的图表类型调用相应的绘图函数
            plot_chart(final_words, f"词语频率{chart_type}", chart_type)
if __name__ == "__main__":
    main()
