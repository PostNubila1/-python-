# -*- coding: utf-8 -*-
"""
VideoRenamer-OCR
基于多时间点 OCR 的批量视频重命名工具（Windows 专用）

功能：
- 对每个视频在多个时间点截图
- 使用 Windows 自带 OCR 识别画面文字
- 从 OCR 结果中提取可能的标题
- 自动重命名视频文件
- 生成 JSON 日志，记录每个文件的处理详情

适用场景：
- 教育视频（课程名、单元名）
- 讲座/会议录像（主题、演讲人）
- 影视/番剧（剧集标题）
- 个人 Vlog（地点、事件）
只需调整“锚点词”和“结束词”即可适配不同内容。
"""

import os
import re
import json
import subprocess
import traceback
from PIL import Image
import winocr

# ================= 配置区域 =================
# 目标视频文件夹（请修改为你的实际路径）
VIDEO_DIR = r"D:\xuexishipin\videos"

# FFmpeg 可执行文件路径。如果已加入系统 PATH，可直接写 "ffmpeg"
FFMPEG_EXE = r"D:\ffmpeg\bin\ffmpeg.exe"

# 尝试截取的时间点（秒）。程序会按顺序尝试，直到成功提取标题。
TIMESTAMPS = [26, 15, 7, 35]

# 日志输出路径
LOG_FILE = os.path.join(VIDEO_DIR, "rename_log.json")
# ============================================


# ================= 关键词配置 =================
# 这些关键词用于定位标题的“起点”。程序会在 OCR 文本中查找这些词，
# 然后从它们之后开始截取标题。你可以根据视频类型增删。
ANCHOR_WORDS = [
    # 教育类
    "课题", "课題", "单元", "单亓", "里元", "地元", "单兀", "第单元",
    # 通用类
    "主题", "题目", "标题", "内容", "讲", "说", "谈", "论",
    # 英文类（如需识别英文视频可保留）
    "Title", "Topic", "Subject", "Lecture", "Lesson",
]

# 这些关键词用于标记标题的“终点”。一旦在标题候选文本中出现，
# 就从该位置截断，避免把无关信息（如学校名、老师名）带入文件名。
END_WORDS = [
    # 中文常见干扰词
    "广州市", "小学", "中学", "老师", "同学", "主讲", "课时",
    "广", "小", "老", "同", "年", "级", "上", "下", "人", "教",
    "版", "第", "课", "电", "视", "台", "育", "局", "例", "（", "(",
    # 英文干扰词
    "School", "Teacher", "Professor", "University", "College",
    "Lecture", "Lesson", "Part", "Chapter",
]

# 如果提取出的标题中包含这些“垃圾词”，则判定为无效，放弃重命名。
GARBAGE_WORDS = [
    "广州", "教育", "小学", "中学", "老师", "同学", "年级",
    "上册", "下册", "版本", "人教", "课程", "课堂",
    # 英文垃圾词
    "School", "Teacher", "University", "Lecture",
]

# 允许的标题最大长度（字符数）。超过则截断。
MAX_TITLE_LEN = 20

# 允许的标题最小长度（字符数）。小于则视为无效。
MIN_TITLE_LEN = 2
# ============================================


def ocr_frame(video_path, timestamp):
    """
    对视频的指定时间点截图，并调用 Windows OCR 识别文字。

    参数:
        video_path: 视频文件路径
        timestamp:  截取时间（秒）

    返回:
        OCR 识别出的文本（字符串）。失败返回空字符串。
    """
    temp_img = os.path.join(VIDEO_DIR, f"temp_{timestamp}.jpg")
    try:
        # 调用 FFmpeg 截取一帧
        cmd = [
            FFMPEG_EXE, "-ss", f"00:00:{timestamp:02d}",
            "-i", video_path, "-frames:v", "1", "-y", temp_img
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 用 PIL 打开图片，交给 winocr 识别
        img = Image.open(temp_img)
        result = winocr.recognize_pil_sync(img, lang='zh-Hans')  # 中文简体
        text = result.get('text', '')
        if not text:
            # 有些版本返回的是 lines 列表
            for line in result.get('lines', []):
                text += line.get('text', '')
        img.close()

        # 清理临时图片
        if os.path.exists(temp_img):
            os.remove(temp_img)
        return text
    except Exception:
        # 任何异常都视为截图或识别失败
        if os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except:
                pass
        return ""


def extract_title(ocr_text):
    """
    从 OCR 文本中提取标题。

    步骤:
        1. 去除所有空白字符，得到连续字符串。
        2. 在文本中查找锚点词（ANCHOR_WORDS），确定标题起点。
        3. 从起点向后扫描，遇到结束词（END_WORDS）就截断。
        4. 清理标题：只保留汉字、字母、冒号，去掉数字和标点。
        5. 校验：长度、垃圾词过滤。
        6. 返回清理后的标题，或空字符串表示失败。
    """
    if not ocr_text:
        return ""

    # 1. 去除空格、换行、制表符等
    text = re.sub(r'[\r\n\t\s]+', '', ocr_text)

    # 2. 寻找锚点
    start = -1
    for anchor in ANCHOR_WORDS:
        idx = text.find(anchor)
        if idx != -1:
            start = idx + len(anchor)  # 从锚点之后开始
            break
    if start == -1:
        return ""  # 没有找到任何锚点，放弃

    # 3. 寻找结束位置
    end = len(text)
    for end_word in END_WORDS:
        idx = text.find(end_word, start)
        if idx != -1 and idx < end:
            end = idx

    # 截取候选标题
    title = text[start:end]

    # 4. 清理：只保留汉字、英文字母和冒号
    title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z：]', '', title)

    # 去掉开头的数字和序数词（如“1”、“第一”等）
    title = re.sub(r'^\d+', '', title)
    title = re.sub(r'^[一二三四五六七八九十]+', '', title)

    # 去掉常见的噪音后缀
    for noise in ['主讲', '教师', '老师', '同学', '大家好', '工作单位']:
        if title.endswith(noise):
            title = title[:-len(noise)]

    title = title.strip()

    # 5. 校验
    if len(title) < MIN_TITLE_LEN:
        return ""
    # 过滤垃圾词
    for g in GARBAGE_WORDS:
        if g in title:
            return ""
    # 过滤纯数字/纯标点
    if re.fullmatch(r'[\d\W]+', title):
        return ""

    # 6. 长度限制
    if len(title) > MAX_TITLE_LEN:
        title = title[:MAX_TITLE_LEN]

    return title


def process_videos():
    """
    主流程：
        1. 遍历 VIDEO_DIR 下所有视频文件。
        2. 对每个视频，依次尝试 TIMESTAMPS 中的时间点进行 OCR。
        3. 提取标题，若成功则重命名，否则跳过。
        4. 记录日志到 JSON 文件，并打印结果。
    """
    try:
        # 支持的视频扩展名
        extensions = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')
        videos = [f for f in os.listdir(VIDEO_DIR)
                  if f.lower().endswith(extensions)]
        if not videos:
            print(f"❌ 在 {VIDEO_DIR} 中没有找到任何视频文件！")
            return

        print(f"共找到 {len(videos)} 个视频，开始处理...\n")
        log_data = []

        for idx, filename in enumerate(videos, 1):
            old_path = os.path.join(VIDEO_DIR, filename)
            print(f"\n[{idx}/{len(videos)}] 处理: {filename}")

            # 用于记录日志的字典
            record = {
                "original_name": filename,
                "ocr": {},
                "extracted_title": "",
                "new_name": filename,
                "status": "跳过",
                "reason": ""
            }

            title = ""
            used_ts = None

            # 依次尝试各个时间点
            for ts in TIMESTAMPS:
                ocr_text = ocr_frame(old_path, ts)
                record["ocr"][str(ts)] = ocr_text
                if ocr_text:
                    t = extract_title(ocr_text)
                    if t:
                        title = t
                        used_ts = ts
                        break  # 成功提取，不再尝试后续时间点

            record["extracted_title"] = title

            if not title:
                record["reason"] = "所有时间点均未提取到有效标题"
                log_data.append(record)
                print("  ⚠️ 跳过：未提取到标题")
                continue

            # 构建新文件名（保留扩展名）
            ext = os.path.splitext(filename)[1]
            new_filename = f"{title}{ext}"
            new_path = os.path.join(VIDEO_DIR, new_filename)

            if new_filename == filename:
                record["reason"] = "名字未变"
                log_data.append(record)
                print("  ⏭️ 跳过：名字未变")
                continue

            # 处理重名：添加 _1、_2 等后缀
            counter = 1
            while os.path.exists(new_path):
                new_filename = f"{title}_{counter}{ext}"
                new_path = os.path.join(VIDEO_DIR, new_filename)
                counter += 1

            # 执行重命名
            try:
                os.rename(old_path, new_path)
                record["status"] = "成功"
                record["new_name"] = new_filename
                log_data.append(record)
                print(f"  ✅ 重命名为: {new_filename}  (来自第{used_ts}秒)")
            except Exception as e:
                record["reason"] = f"重命名失败: {e}"
                log_data.append(record)
                print(f"  ❌ 失败：{e}")

        # 保存日志
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ 详细日志已保存至: {LOG_FILE}")

        # 汇总统计
        success = sum(1 for r in log_data if r['status'] == '成功')
        skip = sum(1 for r in log_data if r['status'] == '跳过')
        print("=" * 60)
        print(f"处理完成！成功: {success} 个 | 跳过: {skip} 个")
        print("=" * 60)

    except Exception as e:
        print("\n❌ 程序运行过程中发生致命错误：")
        traceback.print_exc()


if __name__ == "__main__":
    process_videos()
    input("\n👉 运行结束，按回车键退出...")