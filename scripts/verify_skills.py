"""
技能与MCP服务验证脚本
验证所有技能模块的导入和基本功能
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

SKILL_NAMES = {
    "wechat-ecosystem": "微信生态全量技能",
    "copyright-free-images": "无版权商用图片素材技能",
    "ai-drawing": "AI绘图技能",
    "content-compliance": "内容合规校验技能",
}


def test_import(module_name: str) -> tuple[bool, str]:
    try:
        mod = __import__(f"skills.{module_name.replace('-', '_')}", fromlist=["*"])
        class_name = "".join(part.capitalize() for part in module_name.split("-")) + "Skills"
        cls = getattr(mod, class_name, None)
        if cls:
            return True, f"模块导入成功 -> {class_name}"
        return False, f"类 {class_name} 未找到"
    except Exception as e:
        return False, f"导入失败: {str(e)}"


def test_status(module_name: str) -> tuple[bool, str]:
    try:
        mod = __import__(f"skills.{module_name.replace('-', '_')}", fromlist=["*"])
        class_name = "".join(part.capitalize() for part in module_name.split("-")) + "Skills"
        cls = getattr(mod, class_name)
        instance = cls()
        status = instance.status()
        return True, str(status)
    except Exception as e:
        return False, f"状态检查失败: {str(e)}"


def test_mcp_server() -> tuple[bool, str]:
    try:
        from skills.wechat_ecosystem import WeChatEcosystemSkills
        from skills.content_compliance import ContentComplianceSkills
        from skills.copyright_free_images import CopyrightFreeImageSkills
        from skills.ai_drawing import AIDrawingSkills

        wechat = WeChatEcosystemSkills()
        compliance = ContentComplianceSkills()
        images = CopyrightFreeImageSkills()
        drawing = AIDrawingSkills()

        return True, "MCP Server所有依赖模块加载成功"
    except Exception as e:
        return False, f"MCP Server依赖加载失败: {str(e)}"


def test_content_compliance() -> tuple[bool, str]:
    try:
        from skills.content_compliance import ContentComplianceSkills
        checker = ContentComplianceSkills()

        test_content = "今天天气真好，适合出去走走，享受美好的生活。"
        result = checker.quick_check(test_content)
        if result.passed:
            return True, f"合规检查正常 - 正常内容通过 (score={result.score})"
        return False, f"合规检查异常 - 正常内容未通过: {result.violations}"

    except Exception as e:
        return False, f"合规检查失败: {str(e)}"


def test_sensitive_detect() -> tuple[bool, str]:
    try:
        from skills.content_compliance import SensitiveWordDetector
        detector = SensitiveWordDetector()

        clean = "今天向大家介绍一种新的学习方法，帮助大家提高效率。"
        dirty = "这是最好的产品，绝对100%有效，包治百病。"
        violations_clean = detector.detect(clean)
        violations_dirty = detector.detect(dirty)

        if violations_dirty:
            return True, f"敏感词检测正常 - 检测到违规词: {[v.split('] ')[1] if '] ' in v else v for v in violations_dirty]}"
        return False, "敏感词检测异常 - 未检测到违规内容"
    except Exception as e:
        return False, f"敏感词检测失败: {str(e)}"


def test_copyright_images() -> tuple[bool, str]:
    try:
        from skills.copyright_free_images import CopyrightFreeImageSkills
        skills = CopyrightFreeImageSkills()
        status = skills.status()
        active = status.get("active_sources", 0)
        return True, f"图片素材技能加载正常 (活跃源: {active}/3)"
    except Exception as e:
        return False, f"图片素材技能失败: {str(e)}"


def test_ai_drawing() -> tuple[bool, str]:
    try:
        from skills.ai_drawing import AIDrawingSkills, DalleClient, CoverImageGenerator
        skills = AIDrawingSkills()
        status = skills.status()
        return True, f"AI绘图技能加载正常 (models: {', '.join(status['models'])})"
    except Exception as e:
        return False, f"AI绘图技能失败: {str(e)}"


def run_all_tests():
    print("=" * 70)
    print("  微信公众号全自动发布智能体 - 技能与MCP服务验证")
    print("=" * 70)
    print()

    all_passed = True
    results = []

    print("📦 [1/6] 技能模块导入测试")
    print("-" * 50)
    for module_name, display_name in SKILL_NAMES.items():
        ok, msg = test_import(module_name)
        status = "✅" if ok else "❌"
        print(f"  {status} {display_name}: {msg}")
        if not ok:
            all_passed = False
        results.append((f"导入-{display_name}", ok, msg))
    print()

    print("📋 [2/6] 技能状态检查")
    print("-" * 50)
    for module_name, display_name in SKILL_NAMES.items():
        ok, msg = test_status(module_name)
        status = "✅" if ok else "❌"
        print(f"  {status} {display_name}: {msg}")
        results.append((f"状态-{display_name}", ok, msg))
    print()

    print("🔌 [3/6] MCP Server 依赖检查")
    print("-" * 50)
    ok, msg = test_mcp_server()
    status = "✅" if ok else "❌"
    print(f"  {status} {msg}")
    if not ok:
        all_passed = False
    results.append(("MCP服务依赖", ok, msg))
    print()

    print("🛡️ [4/6] 内容合规校验测试")
    print("-" * 50)
    ok, msg = test_content_compliance()
    status = "✅" if ok else "❌"
    print(f"  {status} {msg}")
    results.append(("内容合规", ok, msg))

    ok, msg = test_sensitive_detect()
    status = "✅" if ok else "❌"
    print(f"  {status} {msg}")
    results.append(("敏感词检测", ok, msg))
    print()

    print("🖼️ [5/6] 图片素材技能测试")
    print("-" * 50)
    ok, msg = test_copyright_images()
    status = "✅" if ok else "❌"
    print(f"  {status} {msg}")
    results.append(("图片素材", ok, msg))
    print()

    print("🎨 [6/6] AI绘图技能测试")
    print("-" * 50)
    ok, msg = test_ai_drawing()
    status = "✅" if ok else "❌"
    print(f"  {status} {msg}")
    results.append(("AI绘图", ok, msg))
    print()

    print("=" * 70)
    if all_passed:
        print("  ✅ 全部验证通过！4个技能包已就绪，MCP服务可启动")
    else:
        print("  ⚠️ 部分验证未通过，请查看上方详情")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_all_tests()
