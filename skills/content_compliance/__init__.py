"""
内容合规校验技能模块 - Content Compliance Check Skills

提供中文内容合规审查能力：
- 敏感词检测与过滤
- AI内容安全审核（调用LLM）
- 中国互联网内容合规校验
- 广告法合规检查
- 内容质量评分
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ComplianceResult:
    passed: bool
    score: float = 100.0
    violations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    risk_level: str = "none"


class SensitiveWordDetector:
    """敏感词检测器"""

    SENSITIVE_PATTERNS = [
        (r"(赌博|博彩|赌场|六合彩|时时彩)", "赌博相关内容"),
        (r"(色情|黄色|成人|激情|一夜情|约炮)", "色情低俗内容"),
        (r"(贩卖|出售|购买.*枪支|购买.*弹药)", "违禁物品"),
        (r"(吸毒|毒品|大麻|海洛因|冰毒|摇头丸)", "毒品相关内容"),
        (r"(传销|拉人头|下线|金字塔)", "传销内容"),
        (r"(高利贷|裸贷|校园贷|套路贷)", "非法借贷"),
        (r"(翻墙|VPN.*免费|科学上网.*免费)", "网络工具违规推广"),
        (r"(代孕|试管婴儿.*包成功|性别选择.*婴儿)", "代孕相关"),
    ]

    AD_LAW_PATTERNS = [
        (r"(最好|第一|唯一|最.*的|顶级|极品|国家级|世界级)", "广告法禁用极限词"),
        (r"(100%|百分百|绝对|彻底|完全.*有效)", "广告法禁用绝对化承诺"),
        (r"(永久|终身|永不|永远)", "广告法禁用时间无限词"),
        (r"(包治|根治|治愈|康复.*保证)", "医疗广告违规用语"),
        (r"(无效退款|保证有效|必有效|一定有效)", "疗效保证违规"),
    ]

    def detect(self, content: str) -> list[str]:
        violations = []
        for pattern, desc in self.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"[敏感内容] {desc}")
        for pattern, desc in self.AD_LAW_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"[广告法] {desc}")
        return violations


class AIContentChecker:
    """AI内容安全审核器"""

    CHECK_PROMPT = """你是一个中文内容安全审核专家。请审查以下文章内容是否存在违规问题。

审查维度：
1. 政治敏感：是否涉及敏感政治话题、领导人负面言论、分裂主义
2. 色情低俗：是否包含性暗示、低俗内容
3. 暴力恐怖：是否包含暴力、血腥、恐怖主义内容
4. 谣言虚假：是否传播未经证实的谣言、虚假信息
5. 广告违规：是否违反广告法（极限词、虚假承诺）
6. 侵权风险：是否涉及抄袭、侵犯知识产权

文章内容：
---
{content}
---

请以JSON格式返回审核结果：
{{"passed": true/false, "violations": ["违规项1", ...], "risk_level": "none/low/medium/high", "suggestions": ["建议1", ...]}}"""

    def __init__(self, api_key: str = "", base_url: str = "https://api.openai.com/v1", model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def check(self, content: str, max_length: int = 4000) -> ComplianceResult:
        if not self.api_key:
            return ComplianceResult(passed=True, score=80.0, risk_level="low",
                                    suggestions=["AI审核未配置API密钥，仅进行规则检查"])

        import requests
        truncated = content[:max_length]
        prompt = self.CHECK_PROMPT.format(content=truncated)
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                return ComplianceResult(passed=True, score=70.0, risk_level="low",
                                        suggestions=["AI审核服务暂时不可用"])
            import json as _json
            result = _json.loads(resp.json()["choices"][0]["message"]["content"])
            return ComplianceResult(
                passed=result.get("passed", True),
                score=100.0 if result.get("passed") else 50.0,
                violations=result.get("violations", []),
                suggestions=result.get("suggestions", []),
                risk_level=result.get("risk_level", "none"),
            )
        except Exception as e:
            return ComplianceResult(passed=True, score=70.0, risk_level="low",
                                    suggestions=[f"AI审核异常: {str(e)}"])


class ContentComplianceSkills:
    """内容合规校验技能 - 统一入口"""

    def __init__(self, ai_api_key: str = "", ai_base_url: str = "https://api.openai.com/v1", ai_model: str = "gpt-4"):
        self.sensitive_detector = SensitiveWordDetector()
        self.ai_checker = AIContentChecker(api_key=ai_api_key, base_url=ai_base_url, model=ai_model)

    def quick_check(self, content: str) -> ComplianceResult:
        """快速合规检查（仅规则匹配）"""
        violations = self.sensitive_detector.detect(content)
        if violations:
            return ComplianceResult(
                passed=False,
                score=max(0, 100 - len(violations) * 15),
                violations=violations,
                suggestions=["请修改以上违规内容后重新提交"],
                risk_level="high" if len(violations) >= 3 else "medium",
            )
        return ComplianceResult(passed=True, score=100.0, risk_level="none")

    def full_check(self, content: str) -> ComplianceResult:
        """完整合规检查（规则 + AI审核）"""
        rule_result = self.quick_check(content)
        if not rule_result.passed:
            return rule_result

        ai_result = self.ai_checker.check(content)
        all_violations = rule_result.violations + ai_result.violations
        all_suggestions = rule_result.suggestions + ai_result.suggestions

        return ComplianceResult(
            passed=ai_result.passed and rule_result.passed,
            score=min(rule_result.score, ai_result.score),
            violations=all_violations,
            suggestions=all_suggestions,
            risk_level=ai_result.risk_level if ai_result.risk_level != "none" else rule_result.risk_level,
        )

    def check_title(self, title: str) -> ComplianceResult:
        """标题合规校验"""
        violations = self.sensitive_detector.detect(title)
        if violations:
            return ComplianceResult(
                passed=False, score=80.0, violations=violations,
                suggestions=["标题存在违规用词，请修改"],
                risk_level="medium",
            )
        return ComplianceResult(passed=True, score=100.0, risk_level="none")

    def status(self) -> dict:
        return {
            "skill": "content-compliance",
            "version": "1.0.0",
            "checkers": {
                "sensitive_word_detector": True,
                "ad_law_checker": True,
                "ai_content_checker": bool(self.ai_checker.api_key),
            },
            "capabilities": [
                "敏感词检测 (quick_check)",
                "广告法合规检查",
                "AI内容安全审核 (full_check)",
                "标题合规校验 (check_title)",
                "风险等级评估",
            ],
            "status": "ready",
        }
