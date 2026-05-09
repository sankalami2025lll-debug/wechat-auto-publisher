/**
 * 微信公众号文章全自动抓取 + 改写 + 保存
 *
 * 用法: node scripts/scrape_and_rewrite.js
 *
 * 流程:
 *   1. Playwright 启动 Chromium 浏览器 → 打开微信文章
 *   2. 等待 JS 渲染完成 → 提取标题/作者/时间/正文/图片
 *   3. 执行规则改写(去AI味+口语化+提高原创度)
 *   4. 保存 Markdown + JSON 到 data/articles/
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTICLE_URL = 'https://mp.weixin.qq.com/s/MgWNAwBDbPNUrBSZc7ZCiQ';
const OUTPUT_DIR = path.join(__dirname, '..', 'data', 'articles');

// ============================================================
//  Part 1: 抓取文章
// ============================================================
async function scrapeArticle() {
  console.log('🕷️  启动 Playwright Chromium...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();

  console.log(`📄 正在加载: ${ARTICLE_URL}`);
  await page.goto(ARTICLE_URL, { waitUntil: 'networkidle', timeout: 30000 });

  // 等待微信正文渲染完成
  await page.waitForSelector('#js_content', { timeout: 15000 }).catch(() => {
    console.log('⚠️  #js_content not found, trying alternative...');
  });
  await page.waitForTimeout(2000);

  // 提取标题
  const title = await page.evaluate(() => {
    const el = document.querySelector('#activity-name') ||
               document.querySelector('.rich_media_title') ||
               document.querySelector('h1');
    return el ? el.innerText.trim() : '';
  });

  // 提取作者/公众号名
  const author = await page.evaluate(() => {
    const el = document.querySelector('#js_name') ||
               document.querySelector('.rich_media_meta_text') ||
               document.querySelector('.profile_nickname');
    return el ? el.innerText.trim() : '';
  });

  // 提取发布时间
  const publishTime = await page.evaluate(() => {
    const el = document.querySelector('#publish_time') ||
               document.querySelector('.rich_media_meta_text');
    const all = document.querySelectorAll('.rich_media_meta_text');
    if (all.length >= 2) return all[all.length - 1].innerText.trim();
    return el ? el.innerText.trim() : '';
  });

  // 提取正文 HTML
  const contentHTML = await page.evaluate(() => {
    const el = document.querySelector('#js_content') ||
               document.querySelector('.rich_media_content') ||
               document.querySelector('.rich_media_area_primary_inner');
    return el ? el.innerHTML.trim() : '';
  });

  // 提取正文纯文本
  const contentText = await page.evaluate(() => {
    const el = document.querySelector('#js_content') ||
               document.querySelector('.rich_media_content');
    return el ? el.innerText.trim() : '';
  });

  // 提取图片
  const images = await page.evaluate(() => {
    const container = document.querySelector('#js_content') ||
                      document.querySelector('.rich_media_content');
    if (!container) return [];
    const imgs = container.querySelectorAll('img');
    return Array.from(imgs).map(img => ({
      src: img.src || img.getAttribute('data-src') || '',
      alt: img.alt || '',
    })).filter(i => i.src && !i.src.includes('data:image/svg'));
  });

  await browser.close();

  const article = { title, author, publishTime, contentHTML, contentText, images };
  console.log(`  ✅ 标题: ${title}`);
  console.log(`  ✅ 作者: ${author}`);
  console.log(`  ✅ 时间: ${publishTime}`);
  console.log(`  ✅ 正文: ${contentText.length} 字符`);
  console.log(`  ✅ 图片: ${images.length} 张`);
  return article;
}

// ============================================================
//  Part 2: AI改写规则 (模拟 ContentRewriter)
// ============================================================
function rewriteContent(article) {
  console.log('\n✍️  执行 AI 改写...');

  let title = article.title;
  let content = article.contentText;

  const stats = {
    originalTitle: article.title,
    originalLength: content.length,
    replacements: [],
  };

  // 规则1: 删除AI套话
  const patternReplacements = [
    { from: /在当今时代[，,]/g, to: '' },
    { from: /值得注意的是[，,]/g, to: '' },
    { from: /综上所述[，,]/g, to: '\n\n总结一下，' },
    { from: /此外[，,]/g, to: '另外，' },
    { from: /与此同时[，,]/g, to: '同时，' },
    { from: /具有里程碑意义/g, to: '很重要' },
    { from: /标志着新篇章/g, to: '开启了新阶段' },
    { from: /在这个快速发展的时代[，,]/g, to: '' },
    { from: /毋庸讳言[，,]/g, to: '' },
    { from: /可谓/g, to: '可以说是' },
    { from: /彰显/g, to: '展示' },
    { from: /突显/g, to: '体现' },
    { from: /赋能/g, to: '帮助' },
    { from: /抓手/g, to: '切入点' },
    { from: /闭环/g, to: '完整流程' },
    { from: /痛点/g, to: '核心问题' },
    { from: /赋能[，,]?/g, to: '帮助，' },
    { from: /依托[于]?/g, to: '依靠' },
    { from: /进一步/g, to: '更进一步' },
    { from: /落地/g, to: '实施' },
    { from: /破局/g, to: '突破' },
  ];

  for (const r of patternReplacements) {
    const before = content;
    content = content.replace(r.from, r.to);
    if (before !== content) {
      stats.replacements.push(`"${r.from}" → "${r.to}"`);
    }
  }

  // 规则2: 打破"首先/其次/最后"公式
  const openingWords = ['首先', '其次', '再次', '最后', '第一', '第二', '第三'];
  let lines = content.split('\n');
  let rewrote = false;
  lines = lines.map((line, i) => {
    const trimmed = line.trim();
    for (const w of openingWords) {
      // Only replace when it's at the start of a paragraph, not in the middle of text
      if (trimmed === w || trimmed === w + '，' || trimmed === w + ',' || trimmed.startsWith(w + '，') || trimmed.startsWith(w + ',')) {
        if (!rewrote) {
          // Replace the first one we find in a sequence
          rewrote = true;
          const rest = trimmed.slice(w.length).replace(/^[，,]/, '').trim();
          if (rest.length > 0) {
            return rest;
          }
          return '首先，' + (line.slice(trimmed.length) || '');
        }
      }
    }
    rewrote = false;
    return line;
  });
  content = lines.join('\n');

  // 规则3: 变化句子节奏 - 合并过短的句子, 拆分过长的句子
  const paragraphs = content.split(/\n{2,}/);
  const variedParagraphs = paragraphs.map(p => {
    const sentences = p.split(/[。！？]/).filter(s => s.trim());
    if (sentences.length === 0) return p;

    // 如果全是短句，合并一些
    if (sentences.every(s => s.length < 15) && sentences.length >= 3) {
      const merged = [];
      for (let i = 0; i < sentences.length; i += 2) {
        if (i + 1 < sentences.length) {
          merged.push(sentences[i].trim() + '，' + sentences[i + 1].trim());
        } else {
          merged.push(sentences[i].trim());
        }
      }
      return merged.join('。') + '。';
    }
    return p;
  });
  content = variedParagraphs.join('\n\n');

  // 规则4: 标题改写 - 更口语化、有吸引力
  const title_replacements = [
    { from: /2025年/g, to: '2025' },
    { from: /发展趋势与展望/g, to: '趋势报告' },
    { from: /深度分析[：:]/g, to: '拆解｜' },
    { from: /全面解读/g, to: '一文看懂' },
  ];
  for (const r of title_replacements) {
    title = title.replace(r.from, r.to);
  }
  // 如果标题超过25字且没有分隔符，加个竖线分隔
  if (title.length > 25 && !title.includes('｜') && !title.includes('|')) {
    const half = Math.floor(title.length / 2);
    // Find a good split point near the middle
    let splitPoint = half;
    for (let i = half; i < title.length - 2; i++) {
      if (title[i] === '，' || title[i] === ',' || title[i] === ' ') {
        splitPoint = i;
        break;
      }
    }
    title = title.slice(0, splitPoint).trim() + '｜' + title.slice(splitPoint).replace(/^[，,\s]+/, '').trim();
  }

  console.log(`  ✅ 标题: ${stats.originalTitle}`);
  console.log(`        → ${title}`);
  console.log(`  ✅ 替换: ${stats.replacements.length} 处`);
  console.log(`  ✅ 字符: ${stats.originalLength} → ${content.length}`);

  return {
    title,
    content,
    summary: article.contentText.slice(0, 200).replace(/\s+/g, ' ').trim() + '...',
    stats,
  };
}

// ============================================================
//  Part 3: 保存文件
// ============================================================
function saveFiles(article, rewritten) {
  console.log('\n💾 保存文件...');

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const safeTitle = rewritten.title.slice(0, 40).replace(/[<>:"/\\|?*#]/g, '').trim() || 'article';
  const baseName = path.join(OUTPUT_DIR, `${timestamp}_${safeTitle}`);

  // Markdown 文件
  const imageList = article.images
    .filter((img, i, arr) => arr.findIndex(x => x.src === img.src) === i) // 去重
    .slice(0, 20)
    .map((img, i) => `${i + 1}. ![](${img.src})`)
    .join('\n');

  const md = [
    `# ${rewritten.title}`,
    '',
    `> **来源**: 微信公众号 · [原文链接](${ARTICLE_URL})`,
    `> **作者**: ${article.author} · **时间**: ${article.publishTime}`,
    `> **改写方式**: 规则引擎 (去AI味 + 口语化 + 提高原创度)`,
    '',
    '---',
    '',
    rewritten.content,
    '',
    '---',
    '',
    '## 🖼️ 图片列表',
    '',
    imageList || '(无图片)',
    '',
    '---',
    '',
    '## 📊 改写对照',
    '',
    `| 指标 | 改写前 | 改写后 |`,
    `|------|--------|--------|`,
    `| 标题 | ${rewritten.stats.originalTitle} | ${rewritten.title} |`,
    `| 正文字数 | ${rewritten.stats.originalLength} 字符 | ${rewritten.content.length} 字符 |`,
    `| AI套话替换 | — | ${rewritten.stats.replacements.length} 处 |`,
    `| 图片数 | ${article.images.length} 张 | ${article.images.length} 张 |`,
    '',
    '### 替换详情',
    ...rewritten.stats.replacements.map(r => `- \`${r}\``),
    '',
  ].join('\n');

  fs.writeFileSync(baseName + '.md', md, 'utf-8');

  // JSON 元数据
  const json = {
    url: ARTICLE_URL,
    platform: 'wechat',
    title_original: rewritten.stats.originalTitle,
    title_rewritten: rewritten.title,
    author: article.author,
    publish_time: article.publishTime,
    content_length_original: rewritten.stats.originalLength,
    content_length_rewritten: rewritten.content.length,
    replacements: rewritten.stats.replacements,
    image_count: article.images.length,
    images: article.images,
    rewritten_at: new Date().toISOString(),
  };

  fs.writeFileSync(baseName + '.json', JSON.stringify(json, null, 2), 'utf-8');

  console.log(`  ✅ Markdown: ${baseName}.md`);
  console.log(`  ✅ JSON:     ${baseName}.json`);

  return { md: baseName + '.md', json: baseName + '.json' };
}

// ============================================================
//  Main
// ============================================================
(async () => {
  console.log('='.repeat(60));
  console.log('  微信公众号全自动抓取 + 改写 + 本地保存');
  console.log('='.repeat(60));
  console.log(`  目标URL: ${ARTICLE_URL}\n`);

  const tStart = Date.now();

  let article;
  try {
    article = await scrapeArticle();
  } catch (err) {
    console.error(`\n  ❌ 抓取失败: ${err.message}`);
    console.error('\n  可能原因:');
    console.error('  1. Playwright/Chromium 安装不完整');
    console.error('  2. 微信反爬拦截了 headless 浏览器');
    console.error('  3. 网络连接问题');
    console.error('\n  尝试: npx playwright install --with-deps chromium');
    process.exit(1);
  }

  const rewritten = rewriteContent(article);
  const paths = saveFiles(article, rewritten);

  const elapsed = ((Date.now() - tStart) / 1000).toFixed(1);
  console.log(`\n⏱️  总耗时: ${elapsed}s`);
  console.log(`📂 输出目录: ${OUTPUT_DIR}`);
  console.log('='.repeat(60));
  console.log('  ✅ 完成！现在可以打开 Markdown 文件查看改写效果');
  console.log('='.repeat(60));
})();
