import os
import requests
import sys

# --- 配置部分 ---
# 后端 API 地址
API_BASE_URL = "http://localhost:8000"

# 管理员用户 ID (必须是数据库中存在的管理员 ID，用于通过权限验证)
ADMIN_USER_ID = 1

# 本地存放 docx 文件的文件夹名称 (请确保此文件夹存在并放入了文件)
LOCAL_KNOWLEDGE_DIR = "本地知识库"


def guess_knowledge_type(filename):
    """根据文件名自动猜测知识类型"""
    if any(keyword in filename for keyword in ["章程", "收费", "分数", "政策", "规定"]):
        return "policy"  # 政策类
    elif "专业介绍" in filename:
        return "major"  # 专业类
    elif any(keyword in filename for keyword in ["校园", "食堂", "宿舍", "环境", "生活"]):
        return "campus"  # 校园生活类
    elif any(keyword in filename for keyword in ["问答", "常见问题", "Q&A"]):
        return "faq"  # 常见问答类
    else:
        return "general"  # 通用类


def upload_files_batch():
    # 1. 检查文件夹是否存在
    if not os.path.exists(LOCAL_KNOWLEDGE_DIR):
        print(f"❌ 错误：找不到文件夹 '{LOCAL_KNOWLEDGE_DIR}'")
        print(f"请在项目根目录下创建一个名为 '{LOCAL_KNOWLEDGE_DIR}' 的文件夹，并把 docx 文件放进去。")
        return

    # 2. 获取文件列表
    files = [f for f in os.listdir(LOCAL_KNOWLEDGE_DIR) if f.endswith(('.docx', '.pdf', '.txt'))]

    if not files:
        print(f"⚠️ 文件夹 '{LOCAL_KNOWLEDGE_DIR}' 是空的，没有找到可上传的文件。")
        return

    print(f"📂 扫描到 {len(files)} 个文件，准备开始上传...\n")
    success_count = 0
    fail_count = 0

    # 3. 遍历上传
    for filename in files:
        file_path = os.path.join(LOCAL_KNOWLEDGE_DIR, filename)
        print(f"--- 正在处理: {filename} ---")

        try:
            # 步骤 A: 上传物理文件
            print("   1. 正在上传文件...", end="", flush=True)
            with open(file_path, 'rb') as f:
                # 注意：API 需要 user_id 参数进行权限验证
                upload_resp = requests.post(
                    f"{API_BASE_URL}/knowledge/upload_file",
                    params={"user_id": ADMIN_USER_ID},
                    files={"file": f}
                )

            if upload_resp.status_code != 200:
                print(f"❌ 失败! 状态码: {upload_resp.status_code}, 错误: {upload_resp.text}")
                fail_count += 1
                continue

            # 获取后端返回的相对路径
            remote_file_path = upload_resp.json().get("file_path")
            print("✅ 成功")

            # 步骤 B: 创建知识条目 (触发抽取)
            print("   2. 创建知识条目并触发抽取...", end="", flush=True)

            knowledge_data = {
                "title": filename.replace(".docx", "").replace(".pdf", ""),
                "type": guess_knowledge_type(filename),
                "file_path": remote_file_path
            }

            create_resp = requests.post(
                f"{API_BASE_URL}/knowledge",
                params={"user_id": ADMIN_USER_ID},  # 同样需要 user_id
                json=knowledge_data
            )

            if create_resp.status_code == 200:
                print(f"✅ 成功 (ID: {create_resp.json().get('id')})")
                success_count += 1
            else:
                print(f"❌ 失败! 状态码: {create_resp.status_code}, 错误: {create_resp.text}")
                fail_count += 1

        except Exception as e:
            print(f"\n❌ 发生异常: {e}")
            fail_count += 1

        print("")  # 空行分隔

    # 4. 总结
    print("=" * 30)
    print(f"🎉 任务完成！")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print("请回到 app.py 的运行窗口查看具体的知识抽取日志。")


if __name__ == "__main__":
    upload_files_batch()