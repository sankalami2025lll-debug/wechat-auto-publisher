/**
 * 深度图片抓取 - 提取微信文章所有图片(含懒加载/隐藏/子图)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ARTICLE_URL = 'https://mp.weixin.qq.com/s/MgWNAwBDbPNUrBSZc7ZCiQ';
const OUTPUT = path.join(__dirname, '..', 'data', 'articles', 'images_captured.json');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  console.log('📄 加载文章...');
  await page.goto(ARTICLE_URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('#js_content', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(3000);

  // 滚动到底部触发懒加载
  await page.evaluate(() => {
    const el = document.querySelector('#js_content') || document.querySelector('.rich_media_content');
    if (el) el.scrollIntoView();
  });
  await page.waitForTimeout(2000);

  // 深度提取所有图片
  const images = await page.evaluate(() => {
    const container = document.querySelector('#js_content') ||
                      document.querySelector('.rich_media_content') ||
                      document.body;

    const imgs = container.querySelectorAll('img');
    const results = [];

    imgs.forEach((img, i) => {
      const src = img.src ||
                  img.getAttribute('data-src') ||
                  img.getAttribute('data-original') ||
                  img.getAttribute('data-url') ||
                  img.getAttribute('data-lazy-src') ||
                  '';
      const style = img.getAttribute('style') || '';
      const classes = img.className || '';
      const parentClasses = img.parentElement ? img.parentElement.className : '';
      const width = img.naturalWidth || img.width || parseInt(img.getAttribute('data-w') || '0');
      const height = img.naturalHeight || img.height || 0;
      const isHidden = style.includes('display:none') ||
                       style.includes('visibility:hidden') ||
                       style.includes('opacity: 0');

      if (src && !src.includes('data:image/svg')) {
        results.push({
          index: i,
          src,
          alt: img.alt || '',
          width,
          height,
          classes,
          parentClasses,
          isHidden,
          isLazy: !!(img.getAttribute('data-src') || img.getAttribute('data-original')),
        });
      }
    });
    return results;
  });

  await browser.close();

  const visible = images.filter(i => !i.isHidden);
  console.log(`\n📸 总图片: ${images.length} 张`);
  console.log(`📸 可见图片: ${visible.length} 张`);
  console.log(`📸 隐藏图片: ${images.filter(i => i.isHidden).length} 张`);

  visible.forEach((img, i) => {
    console.log(`\n  [${i+1}] ${img.width}x${img.height}`);
    console.log(`      src: ${img.src.slice(0, 100)}...`);
    if (img.alt) console.log(`      alt: ${img.alt}`);
    console.log(`      class: ${img.classes || '(none)'}`);
    console.log(`      parent: ${img.parentClasses || '(none)'}`);
  });

  fs.writeFileSync(OUTPUT, JSON.stringify({ total: images.length, visible: visible.length, images: visible }, null, 2));
  console.log(`\n✅ 已保存: ${OUTPUT}`);
})();
