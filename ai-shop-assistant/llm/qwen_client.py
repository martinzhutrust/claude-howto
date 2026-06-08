"""Qwen (通义千问) LLM 客户端。

使用 DashScope 的 OpenAI 兼容端点，支持流式输出。
模型推荐：qwen-max（最强）或 qwen-plus（性价比高）。
"""
from __future__ import annotations

import os

from openai import AsyncOpenAI


class QwenClient:
    def __init__(
        self,
        api_key: str,
        model: str = "qwen-max",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    async def chat(self, user_prompt: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def stream_chat(self, user_prompt: str, system_prompt: str | None = None):
        """流式返回，适合实时展示。逐块 yield str。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def aclose(self) -> None:
        await self._client.close()


def build_qwen_client() -> QwenClient:
    return QwenClient(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model=os.environ.get("QWEN_MODEL", "qwen-max"),
        temperature=float(os.environ.get("QWEN_TEMPERATURE", "0.3")),
    )
