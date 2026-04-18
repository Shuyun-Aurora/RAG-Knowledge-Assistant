# backend/service/agent_service.py

from typing import Dict, List
from dto.schemas import AgentStyle, AgentStyleConfig


class AgentService:
    """角色化Agent服务"""

    def __init__(self):
        self.agent_styles = self._initialize_agent_styles()

    def _initialize_agent_styles(self) -> Dict[AgentStyle, AgentStyleConfig]:
        """初始化所有agent风格配置"""
        styles = {
            AgentStyle.DEFAULT: AgentStyleConfig(
                style=AgentStyle.DEFAULT,
                name="默认助手",
                description="标准AI助手，提供准确、客观的回答",
                system_prompt='你是一个AI助教。请严格根据下面提供的"背景知识"来回答"问题"。',
                personality_traits=["客观", "准确", "专业"]
            ),

            AgentStyle.STRICT_TUTOR: AgentStyleConfig(
                style=AgentStyle.STRICT_TUTOR,
                name="严谨导师",
                description="严格、严谨的导师风格，注重学术规范和准确性",
                system_prompt="""你是一位严谨的学术导师。你的回答应该：
                1. 严格基于提供的背景知识
                2. 注重学术规范和准确性
                3. 使用专业术语和严谨的表达
                4. 在必要时指出概念的重要性
                5. 鼓励学生深入思考

                请根据以下背景知识回答用户问题：""",
                personality_traits=["严谨", "学术", "专业", "严格"]
            ),

            AgentStyle.FRIENDLY_PEER: AgentStyleConfig(
                style=AgentStyle.FRIENDLY_PEER,
                name="热心同学",
                description="友好、亲切的同学风格，用轻松易懂的方式解释概念",
                system_prompt="""你是一位热心的同学，用友好、亲切的语气帮助其他同学学习。你的回答应该：
                1. 使用轻松、易懂的语言
                2. 分享学习心得和经验
                3. 鼓励和激励同学
                4. 用生活中的例子来解释概念
                5. 营造轻松愉快的学习氛围

                请根据以下背景知识回答用户问题：""",
                personality_traits=["友好", "亲切", "鼓励", "易懂"]
            ),
        }
        return styles

    def get_agent_style_config(self, style: AgentStyle) -> AgentStyleConfig:
        """获取指定风格的配置"""
        return self.agent_styles.get(style, self.agent_styles[AgentStyle.DEFAULT])

    def get_all_agent_styles(self) -> List[AgentStyleConfig]:
        """获取所有可用的agent风格"""
        return list(self.agent_styles.values())

    def generate_prompt(self, style: AgentStyle, rag_context: str, question: str, history_str: str = "", kg_context: str = None) -> str:
        """根据风格生成相应的prompt，支持知识图谱信息"""
        style_config = self.get_agent_style_config(style)

        prompt_parts = [
            f"{style_config.system_prompt}\n",
            "【重要规则】：如果\"背景知识\"与\"问题\"或\"历史对话\"完全无关或没有背景知识等信息，请忽略\"背景知识\"，并明确告诉用户：\"我找到的课程资料似乎与您的问题无关，但我可以尝试回答。\"\n"
        ]
        
        # 只有当history_str不为空时才添加历史对话部分
        if history_str and history_str.strip():
            prompt_parts.append(f"历史对话:\n{history_str}\n")
        
        # 只有当context不为空时才添加背景知识部分
        if rag_context and rag_context.strip():
            prompt_parts.append(f"背景知识:\n{rag_context}\n")

        # 只有当kg_context不为空时才添加知识图谱部分
        if kg_context and kg_context.strip():
            prompt_parts.extend([
                "知识图谱信息:",
                kg_context,
                "",
                "请结合背景知识和知识图谱中的结构化关系，提供准确、详细的回答。",
                "注意利用知识图谱中的概念关系、算法规则等结构化信息。"
            ])

        prompt_parts.append(f"问题: {question}\n")

        return "\n".join(prompt_parts)

    def get_style_description(self, style: AgentStyle) -> str:
        """获取风格描述"""
        config = self.get_agent_style_config(style)
        return f"{config.name}: {config.description}"