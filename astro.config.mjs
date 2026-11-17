// @ts-nocheck — 配置使用 Node 全局 process.env（构建期注入 SITE_URL/URL/CF_PAGES_URL），项目未引入 @types/node
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// 站点地址按部署环境注入，避免把单一平台域名写死（国内/国外两个部署各自生效）：
//   1) SITE_URL       手动指定（自定义域名，或无自动注入的平台）
//   2) URL            Netlify 构建时自动注入（主域名）
//   3) CF_PAGES_URL   Cloudflare Pages 构建时自动注入（.pages.dev 域名）
// 本地未设置时不生成绝对 canonical（Astro.site 为 undefined，走相对路径）。
const site = process.env.SITE_URL || process.env.URL || process.env.CF_PAGES_URL;

export default defineConfig({
  site,
  output: 'static',
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
