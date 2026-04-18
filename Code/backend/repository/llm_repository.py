from typing import Any, Dict, Optional, AsyncGenerator
import requests
import aiohttp
import asyncio
import os
import base64
from langchain_core.runnables import Runnable
from langchain_core.prompt_values import ChatPromptValue
from openai import OpenAI


class QwenVision:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(
            api_key=api_key or os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def analyze_image(self, image_data_url: str, type: str):
        if type == "image":
            prompt = "请详细描述这张图片的内容"
        elif type == "equation":
            prompt = "解析这个图片中的公式，返回latex格式（不要任何其他内容）"
        elif type == "table":
            prompt = "解析这个图片中的表格，返回latex格式（不要任何其他内容）"
        messages = [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {"type": "text", "text": prompt}
            ]}
        ]
        completion = self.client.chat.completions.create(
            model="qwen-vl-plus",
            messages=messages
        )
        return completion.choices[0].message.content


def encode_image_to_base64(image_path: str) -> str:
    """支持多种图片类型的base64编码"""
    ext = os.path.splitext(image_path)[-1].lower()
    mime = "image/jpeg"
    if ext == ".png":
        mime = "image/png"
    elif ext == ".gif":
        mime = "image/gif"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


class DeepSeekLLM(Runnable):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "deepseek-chat"
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def invoke(
            self,
            input: Dict[str, Any] | str | ChatPromptValue,
            config: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> str:
        # 处理不同类型的输入
        if isinstance(input, ChatPromptValue):
            prompt = "\n".join([m.content for m in input.messages])
        elif isinstance(input, str):
            prompt = input
        else:  # 假设是字典
            prompt = input.get("question", input.get("input", ""))

        # 调用DeepSeek API
        response = requests.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=60  # 添加超时设置
        )
        response.raise_for_status()  # 检查HTTP错误
        return response.json()["choices"][0]["message"]["content"]

    async def stream_invoke(
            self,
            input: Dict[str, Any] | str | ChatPromptValue,
            config: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        流式调用DeepSeek API
        """
        # 处理不同类型的输入
        if isinstance(input, ChatPromptValue):
            prompt = "\n".join([m.content for m in input.messages])
        elif isinstance(input, str):
            prompt = input
        else:  # 假设是字典
            prompt = input.get("question", input.get("input", ""))

        # 使用aiohttp进行异步HTTP请求
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "stream": True
                    },
                    timeout=aiohttp.ClientTimeout(total=120)  # 2分钟超时
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data = line_str[6:]  # 移除 'data: ' 前缀
                                if data == '[DONE]':
                                    break
                                try:
                                    import json
                                    chunk = json.loads(data)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        if 'content' in delta:
                                            yield delta['content']
                                except json.JSONDecodeError:
                                    continue
                                except Exception as e:
                                    print(f"处理流式数据时出错: {e}")
                                    continue
                                    
            except aiohttp.ClientError as e:
                print(f"HTTP请求错误: {e}")
                yield f"错误: 无法连接到AI服务 ({str(e)})"
            except asyncio.TimeoutError:
                print("请求超时")
                yield "错误: 请求超时，请稍后重试"
            except Exception as e:
                print(f"流式调用时发生未知错误: {e}")
                yield f"错误: {str(e)}"
