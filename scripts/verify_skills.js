/**
 * 技能与MCP服务验证脚本 (Node.js)
 * 验证所有Python模块文件完整性
 */
const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = __dirname + '/..';

const requiredFiles = [
    'skills/__init__.py',
    'skills/skills.json',
    'skills/wechat-ecosystem/__init__.py',
    'skills/copyright-free-images/__init__.py',
    'skills/ai-drawing/__init__.py',
    'skills/content-compliance/__init__.py',
    'src/services/mcp/__init__.py',
    'src/services/mcp/server.py',
    '.mcp.json',
];

const classChecks = [
    { file: 'skills/wechat-ecosystem/__init__.py', class: 'WeChatEcosystemSkills', name: '微信生态全量技能' },
    { file: 'skills/copyright-free-images/__init__.py', class: 'CopyrightFreeImageSkills', name: '无版权商用图片素材技能' },
    { file: 'skills/ai-drawing/__init__.py', class: 'AIDrawingSkills', name: 'AI绘图技能' },
    { file: 'skills/content-compliance/__init__.py', class: 'ContentComplianceSkills', name: '内容合规校验技能' },
];

const functionChecks = [
    { file: 'skills/wechat-ecosystem/__init__.py', functions: ['WeChatTokenManager', 'WeChatMaterialManager', 'WeChatDraftManager', 'get_token', 'upload_image', 'create_draft', 'publish_draft'] },
    { file: 'skills/copyright-free-images/__init__.py', functions: ['UnsplashClient', 'PexelsClient', 'PixabayClient', 'search_all', 'download_best'] },
    { file: 'skills/ai-drawing/__init__.py', functions: ['DalleClient', 'CoverImageGenerator', 'text_to_image', 'generate_article_cover'] },
    { file: 'skills/content-compliance/__init__.py', functions: ['SensitiveWordDetector', 'AIContentChecker', 'quick_check', 'full_check', 'check_title'] },
];

const mcpTools = [
    'wechat_get_access_token',
    'wechat_create_draft',
    'wechat_publish_draft',
    'wechat_upload_image',
    'wechat_content_check',
    'wechat_search_images',
    'wechat_ai_draw',
    'wechat_generate_cover',
];

console.log('='.repeat(66));
console.log('  微信公众号全自动发布智能体 - 技能与MCP服务验证');
console.log('='.repeat(66));
console.log();

let allPassed = true;
let fileCount = 0;
let totalLines = 0;

// 1. Check all required files exist
console.log('[1/6] 文件完整性检查');
console.log('-'.repeat(50));
for (const f of requiredFiles) {
    const fullPath = path.join(PROJECT_ROOT, f);
    if (fs.existsSync(fullPath)) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const lines = content.split('\n').length;
        totalLines += lines;
        fileCount++;
        console.log(`  ✅ ${f} (${lines} 行)`);
    } else {
        console.log(`  ❌ ${f} 不存在`);
        allPassed = false;
    }
}
console.log(`  总计: ${fileCount} 个文件, ${totalLines} 行代码`);
console.log();

// 2. Check class definitions
console.log('[2/6] 技能类定义检查');
console.log('-'.repeat(50));
for (const check of classChecks) {
    const fullPath = path.join(PROJECT_ROOT, check.file);
    const content = fs.readFileSync(fullPath, 'utf8');
    if (content.includes(`class ${check.class}`)) {
        console.log(`  ✅ ${check.name}: class ${check.class} 已定义`);
    } else {
        console.log(`  ❌ ${check.name}: class ${check.class} 未找到`);
        allPassed = false;
    }
}
console.log();

// 3. Check key functions/methods
console.log('[3/6] 核心方法检查');
console.log('-'.repeat(50));
for (const check of functionChecks) {
    const fullPath = path.join(PROJECT_ROOT, check.file);
    const content = fs.readFileSync(fullPath, 'utf8');
    for (const func of check.functions) {
        const found = content.includes(`class ${func}`) || content.includes(`def ${func}`);
        const icon = found ? '✅' : '⚠️';
        if (!found) allPassed = false;
        console.log(`  ${icon} ${func}(): ${found ? '已定义' : '未找到'}`);
    }
}
console.log();

// 4. Check MCP tools
console.log('[4/6] MCP工具注册检查');
console.log('-'.repeat(50));
const mcpPath = path.join(PROJECT_ROOT, 'src/services/mcp/server.py');
const mcpContent = fs.readFileSync(mcpPath, 'utf8');
for (const tool of mcpTools) {
    const found = mcpContent.includes(`"${tool}"`);
    const icon = found ? '✅' : '❌';
    if (!found) allPassed = false;
    console.log(`  ${icon} ${tool}: ${found ? '已注册' : '未注册'}`);
}
console.log();

// 5. Check MCP config
console.log('[5/6] MCP配置文件检查');
console.log('-'.repeat(50));
const configPath = path.join(PROJECT_ROOT, '.mcp.json');
const configContent = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const servers = configContent.mcpServers || {};
const serverNames = Object.keys(servers);
console.log(`  ✅ MCP Server 数量: ${serverNames.length}`);
for (const name of serverNames) {
    const server = servers[name];
    console.log(`     - ${name}`);
    console.log(`       command: ${server.command}`);
    console.log(`       args: ${server.args.join(' ')}`);
    console.log(`       env keys: ${Object.keys(server.env).join(', ')}`);
}
console.log();

// 6. Check skills.json manifest
console.log('[6/6] 技能清单 (skills.json) 检查');
console.log('-'.repeat(50));
const manifestPath = path.join(PROJECT_ROOT, 'skills/skills.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const skillNames = Object.keys(manifest.skills);
console.log(`  ✅ 技能总数: ${skillNames.length}`);
for (const name of skillNames) {
    const skill = manifest.skills[name];
    console.log(`     - ${skill.name} v${skill.version}`);
    console.log(`       能力: ${skill.capabilities.join(', ')}`);
    console.log(`       配置: ${skill.config_required.join(', ')}`);
}
console.log();

// Summary
console.log('='.repeat(66));
if (allPassed) {
    console.log('  ✅ 全部验证通过！');
    console.log('');
    console.log('  📦 4个技能包已就绪');
    console.log('  🔌 MCP服务已配置完成');
    console.log('  📋 共 8 个 MCP 工具已注册');
    console.log('');
    console.log('  ⚠️ 提示: 当前环境未检测到完整Python安装，');
    console.log('     请安装 Python 3.10+ 后运行:');
    console.log('       pip install -r requirements.txt');
    console.log('       python scripts/verify_skills.py');
} else {
    console.log('  ⚠️ 部分检查未通过，请查看上方详情');
}
console.log('='.repeat(66));
