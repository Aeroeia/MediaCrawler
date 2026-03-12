import { resolveComponent, useSSRContext } from "vue";
import { ssrRenderAttrs, ssrRenderSuspense, ssrRenderComponent, ssrRenderStyle } from "vue/server-renderer";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"MediaCrawler 项目架构文档","description":"","frontmatter":{},"headers":[],"relativePath":"项目架构文档.md","filePath":"项目架构文档.md","lastUpdated":1772551867000}');
const _sfc_main = { name: "项目架构文档.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  const _component_Mermaid = resolveComponent("Mermaid");
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="mediacrawler-项目架构文档" tabindex="-1">MediaCrawler 项目架构文档 <a class="header-anchor" href="#mediacrawler-项目架构文档" aria-label="Permalink to &quot;MediaCrawler 项目架构文档&quot;">​</a></h1><blockquote><p>入门建议：如果你是 Python 新手，先阅读 <a href="./零基础源码导读.html">零基础源码导读</a>，再回到本页看整体架构。</p></blockquote><h2 id="_1-项目概述" tabindex="-1">1. 项目概述 <a class="header-anchor" href="#_1-项目概述" aria-label="Permalink to &quot;1. 项目概述&quot;">​</a></h2><h3 id="_1-1-项目简介" tabindex="-1">1.1 项目简介 <a class="header-anchor" href="#_1-1-项目简介" aria-label="Permalink to &quot;1.1 项目简介&quot;">​</a></h3><p>MediaCrawler 是一个多平台自媒体爬虫框架，采用 Python 异步编程实现，支持爬取主流社交媒体平台的内容、评论和创作者信息。</p><h3 id="_1-2-支持的平台" tabindex="-1">1.2 支持的平台 <a class="header-anchor" href="#_1-2-支持的平台" aria-label="Permalink to &quot;1.2 支持的平台&quot;">​</a></h3><table tabindex="0"><thead><tr><th>平台</th><th>代号</th><th>主要功能</th></tr></thead><tbody><tr><td>小红书</td><td><code>xhs</code></td><td>笔记搜索、详情、创作者</td></tr><tr><td>抖音</td><td><code>dy</code></td><td>视频搜索、详情、创作者</td></tr><tr><td>快手</td><td><code>ks</code></td><td>视频搜索、详情、创作者</td></tr><tr><td>B站</td><td><code>bili</code></td><td>视频搜索、详情、UP主</td></tr><tr><td>微博</td><td><code>wb</code></td><td>微博搜索、详情、博主</td></tr><tr><td>百度贴吧</td><td><code>tieba</code></td><td>帖子搜索、详情</td></tr><tr><td>知乎</td><td><code>zhihu</code></td><td>问答搜索、详情、答主</td></tr></tbody></table><h3 id="_1-3-核心功能特性" tabindex="-1">1.3 核心功能特性 <a class="header-anchor" href="#_1-3-核心功能特性" aria-label="Permalink to &quot;1.3 核心功能特性&quot;">​</a></h3><ul><li><strong>多平台支持</strong>：统一的爬虫接口，支持 7 大主流平台</li><li><strong>多种登录方式</strong>：二维码、手机号、Cookie 三种登录方式</li><li><strong>多种存储方式</strong>：CSV、JSON、JSONL、SQLite、MySQL、MongoDB、Excel</li><li><strong>反爬虫对策</strong>：CDP 模式、代理 IP 池、请求签名</li><li><strong>异步高并发</strong>：基于 asyncio 的异步架构，高效并发爬取</li><li><strong>词云生成</strong>：自动生成评论词云图</li></ul><hr><h2 id="_2-系统架构总览" tabindex="-1">2. 系统架构总览 <a class="header-anchor" href="#_2-系统架构总览" aria-label="Permalink to &quot;2. 系统架构总览&quot;">​</a></h2><h3 id="_2-1-高层架构图" tabindex="-1">2.1 高层架构图 <a class="header-anchor" href="#_2-1-高层架构图" aria-label="Permalink to &quot;2.1 高层架构图&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-156",
        class: "mermaid",
        graph: "flowchart%20TB%0A%20%20%20%20subgraph%20Entry%5B%22%E5%85%A5%E5%8F%A3%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20main%5B%22main.py%3Cbr%2F%3E%E7%A8%8B%E5%BA%8F%E5%85%A5%E5%8F%A3%22%5D%0A%20%20%20%20%20%20%20%20cmdarg%5B%22cmd_arg%3Cbr%2F%3E%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%8F%82%E6%95%B0%22%5D%0A%20%20%20%20%20%20%20%20config%5B%22config%3Cbr%2F%3E%E9%85%8D%E7%BD%AE%E7%AE%A1%E7%90%86%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Core%5B%22%E6%A0%B8%E5%BF%83%E7%88%AC%E8%99%AB%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20factory%5B%22CrawlerFactory%3Cbr%2F%3E%E7%88%AC%E8%99%AB%E5%B7%A5%E5%8E%82%22%5D%0A%20%20%20%20%20%20%20%20base%5B%22AbstractCrawler%3Cbr%2F%3E%E7%88%AC%E8%99%AB%E5%9F%BA%E7%B1%BB%22%5D%0A%0A%20%20%20%20%20%20%20%20subgraph%20Platforms%5B%22%E5%B9%B3%E5%8F%B0%E5%AE%9E%E7%8E%B0%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20xhs%5B%22XiaoHongShuCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20dy%5B%22DouYinCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20ks%5B%22KuaishouCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20bili%5B%22BilibiliCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20wb%5B%22WeiboCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20tieba%5B%22TieBaCrawler%22%5D%0A%20%20%20%20%20%20%20%20%20%20%20%20zhihu%5B%22ZhihuCrawler%22%5D%0A%20%20%20%20%20%20%20%20end%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Client%5B%22API%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20absClient%5B%22AbstractApiClient%3Cbr%2F%3E%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%9F%BA%E7%B1%BB%22%5D%0A%20%20%20%20%20%20%20%20xhsClient%5B%22XiaoHongShuClient%22%5D%0A%20%20%20%20%20%20%20%20dyClient%5B%22DouYinClient%22%5D%0A%20%20%20%20%20%20%20%20ksClient%5B%22KuaiShouClient%22%5D%0A%20%20%20%20%20%20%20%20biliClient%5B%22BilibiliClient%22%5D%0A%20%20%20%20%20%20%20%20wbClient%5B%22WeiboClient%22%5D%0A%20%20%20%20%20%20%20%20tiebaClient%5B%22BaiduTieBaClient%22%5D%0A%20%20%20%20%20%20%20%20zhihuClient%5B%22ZhiHuClient%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Storage%5B%22%E6%95%B0%E6%8D%AE%E5%AD%98%E5%82%A8%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20storeFactory%5B%22StoreFactory%3Cbr%2F%3E%E5%AD%98%E5%82%A8%E5%B7%A5%E5%8E%82%22%5D%0A%20%20%20%20%20%20%20%20csv%5B%22CSV%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20json%5B%22JSON%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20sqlite%5B%22SQLite%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20mysql%5B%22MySQL%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20mongodb%5B%22MongoDB%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20excel%5B%22Excel%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Infra%5B%22%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20browser%5B%22%E6%B5%8F%E8%A7%88%E5%99%A8%E7%AE%A1%E7%90%86%3Cbr%2F%3EPlaywright%2FCDP%22%5D%0A%20%20%20%20%20%20%20%20proxy%5B%22%E4%BB%A3%E7%90%86IP%E6%B1%A0%22%5D%0A%20%20%20%20%20%20%20%20cache%5B%22%E7%BC%93%E5%AD%98%E7%B3%BB%E7%BB%9F%22%5D%0A%20%20%20%20%20%20%20%20login%5B%22%E7%99%BB%E5%BD%95%E7%AE%A1%E7%90%86%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20main%20--%3E%20factory%0A%20%20%20%20cmdarg%20--%3E%20main%0A%20%20%20%20config%20--%3E%20main%0A%20%20%20%20factory%20--%3E%20base%0A%20%20%20%20base%20--%3E%20Platforms%0A%20%20%20%20Platforms%20--%3E%20Client%0A%20%20%20%20Client%20--%3E%20Storage%0A%20%20%20%20Client%20--%3E%20Infra%0A%20%20%20%20Storage%20--%3E%20storeFactory%0A%20%20%20%20storeFactory%20--%3E%20csv%20%26%20json%20%26%20sqlite%20%26%20mysql%20%26%20mongodb%20%26%20excel%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_2-2-数据流向图" tabindex="-1">2.2 数据流向图 <a class="header-anchor" href="#_2-2-数据流向图" aria-label="Permalink to &quot;2.2 数据流向图&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-160",
        class: "mermaid",
        graph: "flowchart%20LR%0A%20%20%20%20subgraph%20Input%5B%22%E8%BE%93%E5%85%A5%22%5D%0A%20%20%20%20%20%20%20%20keywords%5B%22%E5%85%B3%E9%94%AE%E8%AF%8D%2FID%22%5D%0A%20%20%20%20%20%20%20%20config%5B%22%E9%85%8D%E7%BD%AE%E5%8F%82%E6%95%B0%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Process%5B%22%E5%A4%84%E7%90%86%E6%B5%81%E7%A8%8B%22%5D%0A%20%20%20%20%20%20%20%20browser%5B%22%E5%90%AF%E5%8A%A8%E6%B5%8F%E8%A7%88%E5%99%A8%22%5D%0A%20%20%20%20%20%20%20%20login%5B%22%E7%99%BB%E5%BD%95%E8%AE%A4%E8%AF%81%22%5D%0A%20%20%20%20%20%20%20%20search%5B%22%E6%90%9C%E7%B4%A2%2F%E7%88%AC%E5%8F%96%22%5D%0A%20%20%20%20%20%20%20%20parse%5B%22%E6%95%B0%E6%8D%AE%E8%A7%A3%E6%9E%90%22%5D%0A%20%20%20%20%20%20%20%20comment%5B%22%E8%8E%B7%E5%8F%96%E8%AF%84%E8%AE%BA%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Output%5B%22%E8%BE%93%E5%87%BA%22%5D%0A%20%20%20%20%20%20%20%20content%5B%22%E5%86%85%E5%AE%B9%E6%95%B0%E6%8D%AE%22%5D%0A%20%20%20%20%20%20%20%20comments%5B%22%E8%AF%84%E8%AE%BA%E6%95%B0%E6%8D%AE%22%5D%0A%20%20%20%20%20%20%20%20creator%5B%22%E5%88%9B%E4%BD%9C%E8%80%85%E6%95%B0%E6%8D%AE%22%5D%0A%20%20%20%20%20%20%20%20media%5B%22%E5%AA%92%E4%BD%93%E6%96%87%E4%BB%B6%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Storage%5B%22%E5%AD%98%E5%82%A8%22%5D%0A%20%20%20%20%20%20%20%20file%5B%22%E6%96%87%E4%BB%B6%E5%AD%98%E5%82%A8%3Cbr%2F%3ECSV%2FJSON%2FExcel%22%5D%0A%20%20%20%20%20%20%20%20db%5B%22%E6%95%B0%E6%8D%AE%E5%BA%93%3Cbr%2F%3ESQLite%2FMySQL%22%5D%0A%20%20%20%20%20%20%20%20nosql%5B%22NoSQL%3Cbr%2F%3EMongoDB%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20keywords%20--%3E%20browser%0A%20%20%20%20config%20--%3E%20browser%0A%20%20%20%20browser%20--%3E%20login%0A%20%20%20%20login%20--%3E%20search%0A%20%20%20%20search%20--%3E%20parse%0A%20%20%20%20parse%20--%3E%20comment%0A%20%20%20%20parse%20--%3E%20content%0A%20%20%20%20comment%20--%3E%20comments%0A%20%20%20%20parse%20--%3E%20creator%0A%20%20%20%20parse%20--%3E%20media%0A%20%20%20%20content%20%26%20comments%20%26%20creator%20--%3E%20file%20%26%20db%20%26%20nosql%0A%20%20%20%20media%20--%3E%20file%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<hr><h2 id="_3-目录结构" tabindex="-1">3. 目录结构 <a class="header-anchor" href="#_3-目录结构" aria-label="Permalink to &quot;3. 目录结构&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>MediaCrawler/</span></span>
<span class="line"><span>├── main.py                 # 程序入口</span></span>
<span class="line"><span>├── var.py                  # 全局上下文变量</span></span>
<span class="line"><span>├── pyproject.toml          # 项目配置</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── base/                   # 基础抽象类</span></span>
<span class="line"><span>│   └── base_crawler.py     # 爬虫、登录、存储、客户端基类</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── config/                 # 配置管理</span></span>
<span class="line"><span>│   ├── base_config.py      # 核心配置</span></span>
<span class="line"><span>│   ├── db_config.py        # 数据库配置</span></span>
<span class="line"><span>│   └── {platform}_config.py # 平台特定配置</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── media_platform/         # 平台爬虫实现</span></span>
<span class="line"><span>│   ├── xhs/                # 小红书</span></span>
<span class="line"><span>│   ├── douyin/             # 抖音</span></span>
<span class="line"><span>│   ├── kuaishou/           # 快手</span></span>
<span class="line"><span>│   ├── bilibili/           # B站</span></span>
<span class="line"><span>│   ├── weibo/              # 微博</span></span>
<span class="line"><span>│   ├── tieba/              # 百度贴吧</span></span>
<span class="line"><span>│   └── zhihu/              # 知乎</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── store/                  # 数据存储</span></span>
<span class="line"><span>│   ├── excel_store_base.py # Excel存储基类</span></span>
<span class="line"><span>│   └── {platform}/         # 各平台存储实现</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── database/               # 数据库层</span></span>
<span class="line"><span>│   ├── models.py           # ORM模型定义</span></span>
<span class="line"><span>│   ├── db_session.py       # 数据库会话管理</span></span>
<span class="line"><span>│   └── mongodb_store_base.py # MongoDB基类</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── proxy/                  # 代理管理</span></span>
<span class="line"><span>│   ├── proxy_ip_pool.py    # IP池管理</span></span>
<span class="line"><span>│   ├── proxy_mixin.py      # 代理刷新混入</span></span>
<span class="line"><span>│   └── providers/          # 代理提供商</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── cache/                  # 缓存系统</span></span>
<span class="line"><span>│   ├── abs_cache.py        # 缓存抽象类</span></span>
<span class="line"><span>│   ├── local_cache.py      # 本地缓存</span></span>
<span class="line"><span>│   └── redis_cache.py      # Redis缓存</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── tools/                  # 工具模块</span></span>
<span class="line"><span>│   ├── app_runner.py       # 应用运行管理</span></span>
<span class="line"><span>│   ├── browser_launcher.py # 浏览器启动</span></span>
<span class="line"><span>│   ├── cdp_browser.py      # CDP浏览器管理</span></span>
<span class="line"><span>│   ├── crawler_util.py     # 爬虫工具</span></span>
<span class="line"><span>│   └── async_file_writer.py # 异步文件写入</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── model/                  # 数据模型</span></span>
<span class="line"><span>│   └── m_{platform}.py     # Pydantic模型</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── libs/                   # JS脚本库</span></span>
<span class="line"><span>│   └── stealth.min.js      # 反检测脚本</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>└── cmd_arg/                # 命令行参数</span></span>
<span class="line"><span>    └── arg.py              # 参数定义</span></span></code></pre></div><hr><h2 id="_4-核心模块详解" tabindex="-1">4. 核心模块详解 <a class="header-anchor" href="#_4-核心模块详解" aria-label="Permalink to &quot;4. 核心模块详解&quot;">​</a></h2><h3 id="_4-1-爬虫基类体系" tabindex="-1">4.1 爬虫基类体系 <a class="header-anchor" href="#_4-1-爬虫基类体系" aria-label="Permalink to &quot;4.1 爬虫基类体系&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-173",
        class: "mermaid",
        graph: "classDiagram%0A%20%20%20%20class%20AbstractCrawler%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Bstart()*%20%E5%90%AF%E5%8A%A8%E7%88%AC%E8%99%AB%0A%20%20%20%20%20%20%20%20%2Bsearch()*%20%E6%90%9C%E7%B4%A2%E5%8A%9F%E8%83%BD%0A%20%20%20%20%20%20%20%20%2Blaunch_browser()%20%E5%90%AF%E5%8A%A8%E6%B5%8F%E8%A7%88%E5%99%A8%0A%20%20%20%20%20%20%20%20%2Blaunch_browser_with_cdp()%20CDP%E6%A8%A1%E5%BC%8F%E5%90%AF%E5%8A%A8%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20AbstractLogin%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Bbegin()*%20%E5%BC%80%E5%A7%8B%E7%99%BB%E5%BD%95%0A%20%20%20%20%20%20%20%20%2Blogin_by_qrcode()*%20%E4%BA%8C%E7%BB%B4%E7%A0%81%E7%99%BB%E5%BD%95%0A%20%20%20%20%20%20%20%20%2Blogin_by_mobile()*%20%E6%89%8B%E6%9C%BA%E5%8F%B7%E7%99%BB%E5%BD%95%0A%20%20%20%20%20%20%20%20%2Blogin_by_cookies()*%20Cookie%E7%99%BB%E5%BD%95%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20AbstractStore%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Bstore_content()*%20%E5%AD%98%E5%82%A8%E5%86%85%E5%AE%B9%0A%20%20%20%20%20%20%20%20%2Bstore_comment()*%20%E5%AD%98%E5%82%A8%E8%AF%84%E8%AE%BA%0A%20%20%20%20%20%20%20%20%2Bstore_creator()*%20%E5%AD%98%E5%82%A8%E5%88%9B%E4%BD%9C%E8%80%85%0A%20%20%20%20%20%20%20%20%2Bstore_image()*%20%E5%AD%98%E5%82%A8%E5%9B%BE%E7%89%87%0A%20%20%20%20%20%20%20%20%2Bstore_video()*%20%E5%AD%98%E5%82%A8%E8%A7%86%E9%A2%91%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20AbstractApiClient%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Brequest()*%20HTTP%E8%AF%B7%E6%B1%82%0A%20%20%20%20%20%20%20%20%2Bupdate_cookies()*%20%E6%9B%B4%E6%96%B0Cookies%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20ProxyRefreshMixin%20%7B%0A%20%20%20%20%20%20%20%20%2Binit_proxy_pool()%20%E5%88%9D%E5%A7%8B%E5%8C%96%E4%BB%A3%E7%90%86%E6%B1%A0%0A%20%20%20%20%20%20%20%20%2B_refresh_proxy_if_expired()%20%E5%88%B7%E6%96%B0%E8%BF%87%E6%9C%9F%E4%BB%A3%E7%90%86%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20XiaoHongShuCrawler%20%7B%0A%20%20%20%20%20%20%20%20%2Bxhs_client%3A%20XiaoHongShuClient%0A%20%20%20%20%20%20%20%20%2Bstart()%0A%20%20%20%20%20%20%20%20%2Bsearch()%0A%20%20%20%20%20%20%20%20%2Bget_specified_notes()%0A%20%20%20%20%20%20%20%20%2Bget_creators_and_notes()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20XiaoHongShuClient%20%7B%0A%20%20%20%20%20%20%20%20%2Bplaywright_page%3A%20Page%0A%20%20%20%20%20%20%20%20%2Bcookie_dict%3A%20Dict%0A%20%20%20%20%20%20%20%20%2Brequest()%0A%20%20%20%20%20%20%20%20%2Bpong()%20%E6%A3%80%E6%9F%A5%E7%99%BB%E5%BD%95%E7%8A%B6%E6%80%81%0A%20%20%20%20%20%20%20%20%2Bget_note_by_keyword()%0A%20%20%20%20%20%20%20%20%2Bget_note_by_id()%0A%20%20%20%20%7D%0A%0A%20%20%20%20AbstractCrawler%20%3C%7C--%20XiaoHongShuCrawler%0A%20%20%20%20AbstractApiClient%20%3C%7C--%20XiaoHongShuClient%0A%20%20%20%20ProxyRefreshMixin%20%3C%7C--%20XiaoHongShuClient%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_4-2-爬虫生命周期" tabindex="-1">4.2 爬虫生命周期 <a class="header-anchor" href="#_4-2-爬虫生命周期" aria-label="Permalink to &quot;4.2 爬虫生命周期&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-177",
        class: "mermaid",
        graph: "sequenceDiagram%0A%20%20%20%20participant%20Main%20as%20main.py%0A%20%20%20%20participant%20Factory%20as%20CrawlerFactory%0A%20%20%20%20participant%20Crawler%20as%20XiaoHongShuCrawler%0A%20%20%20%20participant%20Browser%20as%20Playwright%2FCDP%0A%20%20%20%20participant%20Login%20as%20XiaoHongShuLogin%0A%20%20%20%20participant%20Client%20as%20XiaoHongShuClient%0A%20%20%20%20participant%20Store%20as%20StoreFactory%0A%0A%20%20%20%20Main-%3E%3EFactory%3A%20create_crawler(%22xhs%22)%0A%20%20%20%20Factory--%3E%3EMain%3A%20crawler%E5%AE%9E%E4%BE%8B%0A%0A%20%20%20%20Main-%3E%3ECrawler%3A%20start()%0A%0A%20%20%20%20alt%20%E5%90%AF%E7%94%A8IP%E4%BB%A3%E7%90%86%0A%20%20%20%20%20%20%20%20Crawler-%3E%3ECrawler%3A%20create_ip_pool()%0A%20%20%20%20end%0A%0A%20%20%20%20alt%20CDP%E6%A8%A1%E5%BC%8F%0A%20%20%20%20%20%20%20%20Crawler-%3E%3EBrowser%3A%20launch_browser_with_cdp()%0A%20%20%20%20else%20%E6%A0%87%E5%87%86%E6%A8%A1%E5%BC%8F%0A%20%20%20%20%20%20%20%20Crawler-%3E%3EBrowser%3A%20launch_browser()%0A%20%20%20%20end%0A%20%20%20%20Browser--%3E%3ECrawler%3A%20browser_context%0A%0A%20%20%20%20Crawler-%3E%3ECrawler%3A%20create_xhs_client()%0A%20%20%20%20Crawler-%3E%3EClient%3A%20pong()%20%E6%A3%80%E6%9F%A5%E7%99%BB%E5%BD%95%E7%8A%B6%E6%80%81%0A%0A%20%20%20%20alt%20%E6%9C%AA%E7%99%BB%E5%BD%95%0A%20%20%20%20%20%20%20%20Crawler-%3E%3ELogin%3A%20begin()%0A%20%20%20%20%20%20%20%20Login-%3E%3ELogin%3A%20login_by_qrcode%2Fmobile%2Fcookie%0A%20%20%20%20%20%20%20%20Login--%3E%3ECrawler%3A%20%E7%99%BB%E5%BD%95%E6%88%90%E5%8A%9F%0A%20%20%20%20end%0A%0A%20%20%20%20alt%20search%E6%A8%A1%E5%BC%8F%0A%20%20%20%20%20%20%20%20Crawler-%3E%3EClient%3A%20get_note_by_keyword()%0A%20%20%20%20%20%20%20%20Client--%3E%3ECrawler%3A%20%E6%90%9C%E7%B4%A2%E7%BB%93%E6%9E%9C%0A%20%20%20%20%20%20%20%20loop%20%E8%8E%B7%E5%8F%96%E8%AF%A6%E6%83%85%0A%20%20%20%20%20%20%20%20%20%20%20%20Crawler-%3E%3EClient%3A%20get_note_by_id()%0A%20%20%20%20%20%20%20%20%20%20%20%20Client--%3E%3ECrawler%3A%20%E7%AC%94%E8%AE%B0%E8%AF%A6%E6%83%85%0A%20%20%20%20%20%20%20%20end%0A%20%20%20%20else%20detail%E6%A8%A1%E5%BC%8F%0A%20%20%20%20%20%20%20%20Crawler-%3E%3EClient%3A%20get_note_by_id()%0A%20%20%20%20else%20creator%E6%A8%A1%E5%BC%8F%0A%20%20%20%20%20%20%20%20Crawler-%3E%3EClient%3A%20get_creator_info()%0A%20%20%20%20end%0A%0A%20%20%20%20Crawler-%3E%3EStore%3A%20store_content%2Fcomment%2Fcreator%0A%20%20%20%20Store--%3E%3ECrawler%3A%20%E5%AD%98%E5%82%A8%E5%AE%8C%E6%88%90%0A%0A%20%20%20%20Main-%3E%3ECrawler%3A%20cleanup()%0A%20%20%20%20Crawler-%3E%3EBrowser%3A%20close()%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_4-3-平台爬虫实现结构" tabindex="-1">4.3 平台爬虫实现结构 <a class="header-anchor" href="#_4-3-平台爬虫实现结构" aria-label="Permalink to &quot;4.3 平台爬虫实现结构&quot;">​</a></h3><p>每个平台目录包含以下核心文件：</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>media_platform/{platform}/</span></span>
<span class="line"><span>├── __init__.py         # 模块导出</span></span>
<span class="line"><span>├── core.py             # 爬虫主实现类</span></span>
<span class="line"><span>├── client.py           # API客户端</span></span>
<span class="line"><span>├── login.py            # 登录实现</span></span>
<span class="line"><span>├── field.py            # 字段/枚举定义</span></span>
<span class="line"><span>├── exception.py        # 异常定义</span></span>
<span class="line"><span>├── help.py             # 辅助函数</span></span>
<span class="line"><span>└── {特殊实现}.py       # 平台特定逻辑</span></span></code></pre></div><h3 id="_4-4-三种爬虫模式" tabindex="-1">4.4 三种爬虫模式 <a class="header-anchor" href="#_4-4-三种爬虫模式" aria-label="Permalink to &quot;4.4 三种爬虫模式&quot;">​</a></h3><table tabindex="0"><thead><tr><th>模式</th><th>配置值</th><th>功能描述</th><th>适用场景</th></tr></thead><tbody><tr><td>搜索模式</td><td><code>search</code></td><td>根据关键词搜索内容</td><td>批量获取特定主题内容</td></tr><tr><td>详情模式</td><td><code>detail</code></td><td>获取指定ID的详情</td><td>精确获取已知内容</td></tr><tr><td>创作者模式</td><td><code>creator</code></td><td>获取创作者所有内容</td><td>追踪特定博主/UP主</td></tr></tbody></table><hr><h2 id="_5-数据存储层" tabindex="-1">5. 数据存储层 <a class="header-anchor" href="#_5-数据存储层" aria-label="Permalink to &quot;5. 数据存储层&quot;">​</a></h2><h3 id="_5-1-存储架构图" tabindex="-1">5.1 存储架构图 <a class="header-anchor" href="#_5-1-存储架构图" aria-label="Permalink to &quot;5.1 存储架构图&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-257",
        class: "mermaid",
        graph: "classDiagram%0A%20%20%20%20class%20AbstractStore%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Bstore_content()*%0A%20%20%20%20%20%20%20%20%2Bstore_comment()*%0A%20%20%20%20%20%20%20%20%2Bstore_creator()*%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20StoreFactory%20%7B%0A%20%20%20%20%20%20%20%20%2BSTORES%3A%20Dict%0A%20%20%20%20%20%20%20%20%2Bcreate_store()%20AbstractStore%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20CsvStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Basync_file_writer%3A%20AsyncFileWriter%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20JsonStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Basync_file_writer%3A%20AsyncFileWriter%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20DbStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Bsession%3A%20AsyncSession%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20SqliteStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Bsession%3A%20AsyncSession%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20MongoStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Bmongo_base%3A%20MongoDBStoreBase%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20ExcelStoreImplement%20%7B%0A%20%20%20%20%20%20%20%20%2Bexcel_base%3A%20ExcelStoreBase%0A%20%20%20%20%20%20%20%20%2Bstore_content()%0A%20%20%20%20%20%20%20%20%2Bstore_comment()%0A%20%20%20%20%7D%0A%0A%20%20%20%20AbstractStore%20%3C%7C--%20CsvStoreImplement%0A%20%20%20%20AbstractStore%20%3C%7C--%20JsonStoreImplement%0A%20%20%20%20AbstractStore%20%3C%7C--%20DbStoreImplement%0A%20%20%20%20AbstractStore%20%3C%7C--%20SqliteStoreImplement%0A%20%20%20%20AbstractStore%20%3C%7C--%20MongoStoreImplement%0A%20%20%20%20AbstractStore%20%3C%7C--%20ExcelStoreImplement%0A%20%20%20%20StoreFactory%20--%3E%20AbstractStore%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_5-2-存储工厂模式" tabindex="-1">5.2 存储工厂模式 <a class="header-anchor" href="#_5-2-存储工厂模式" aria-label="Permalink to &quot;5.2 存储工厂模式&quot;">​</a></h3><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 以抖音为例</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">class</span><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}"> DouyinStoreFactory</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">:</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">    STORES</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}"> {</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;csv&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinCsvStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;db&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinDbStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;json&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinJsonStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;sqlite&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinSqliteStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;mongodb&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinMongoStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">        &quot;excel&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">: DouyinExcelStoreImplement,</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">    }</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}">    @</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">staticmethod</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">    def</span><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}"> create_store</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">() -&gt; AbstractStore:</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">        store_class </span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">=</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}"> DouyinStoreFactory.</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">STORES</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">.get(config.</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">SAVE_DATA_OPTION</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">)</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">        return</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}"> store_class()</span></span></code></pre></div><h3 id="_5-3-存储方式对比" tabindex="-1">5.3 存储方式对比 <a class="header-anchor" href="#_5-3-存储方式对比" aria-label="Permalink to &quot;5.3 存储方式对比&quot;">​</a></h3><table tabindex="0"><thead><tr><th>存储方式</th><th>配置值</th><th>优点</th><th>适用场景</th></tr></thead><tbody><tr><td>CSV</td><td><code>csv</code></td><td>简单、通用</td><td>小规模数据、快速查看</td></tr><tr><td>JSON</td><td><code>json</code></td><td>结构完整、易解析</td><td>API对接、数据交换</td></tr><tr><td>JSONL</td><td><code>jsonl</code></td><td>追加写入、性能好</td><td>大规模数据、增量爬取（默认）</td></tr><tr><td>SQLite</td><td><code>sqlite</code></td><td>轻量、无需服务</td><td>本地开发、小型项目</td></tr><tr><td>MySQL</td><td><code>db</code></td><td>性能好、支持并发</td><td>生产环境、大规模数据</td></tr><tr><td>MongoDB</td><td><code>mongodb</code></td><td>灵活、易扩展</td><td>非结构化数据、快速迭代</td></tr><tr><td>Excel</td><td><code>excel</code></td><td>可视化、易分享</td><td>报告、数据分析</td></tr></tbody></table><hr><h2 id="_6-基础设施层" tabindex="-1">6. 基础设施层 <a class="header-anchor" href="#_6-基础设施层" aria-label="Permalink to &quot;6. 基础设施层&quot;">​</a></h2><h3 id="_6-1-代理系统架构" tabindex="-1">6.1 代理系统架构 <a class="header-anchor" href="#_6-1-代理系统架构" aria-label="Permalink to &quot;6.1 代理系统架构&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-390",
        class: "mermaid",
        graph: "flowchart%20TB%0A%20%20%20%20subgraph%20Config%5B%22%E9%85%8D%E7%BD%AE%22%5D%0A%20%20%20%20%20%20%20%20enable%5B%22ENABLE_IP_PROXY%22%5D%0A%20%20%20%20%20%20%20%20provider%5B%22IP_PROXY_PROVIDER%22%5D%0A%20%20%20%20%20%20%20%20count%5B%22IP_PROXY_POOL_COUNT%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Pool%5B%22%E4%BB%A3%E7%90%86%E6%B1%A0%E7%AE%A1%E7%90%86%22%5D%0A%20%20%20%20%20%20%20%20pool%5B%22ProxyIpPool%22%5D%0A%20%20%20%20%20%20%20%20load%5B%22load_proxies()%22%5D%0A%20%20%20%20%20%20%20%20validate%5B%22_is_valid_proxy()%22%5D%0A%20%20%20%20%20%20%20%20get%5B%22get_proxy()%22%5D%0A%20%20%20%20%20%20%20%20refresh%5B%22get_or_refresh_proxy()%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Providers%5B%22%E4%BB%A3%E7%90%86%E6%8F%90%E4%BE%9B%E5%95%86%22%5D%0A%20%20%20%20%20%20%20%20kuaidl%5B%22%E5%BF%AB%E4%BB%A3%E7%90%86%3Cbr%2F%3EKuaiDaiLiProxy%22%5D%0A%20%20%20%20%20%20%20%20wandou%5B%22%E4%B8%87%E4%BB%A3%E7%90%86%3Cbr%2F%3EWanDouHttpProxy%22%5D%0A%20%20%20%20%20%20%20%20jishu%5B%22%E6%8A%80%E6%9C%AFIP%3Cbr%2F%3EJiShuHttpProxy%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Client%5B%22API%E5%AE%A2%E6%88%B7%E7%AB%AF%22%5D%0A%20%20%20%20%20%20%20%20mixin%5B%22ProxyRefreshMixin%22%5D%0A%20%20%20%20%20%20%20%20request%5B%22request()%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20enable%20--%3E%20pool%0A%20%20%20%20provider%20--%3E%20Providers%0A%20%20%20%20count%20--%3E%20load%0A%20%20%20%20pool%20--%3E%20load%0A%20%20%20%20load%20--%3E%20validate%0A%20%20%20%20validate%20--%3E%20Providers%0A%20%20%20%20pool%20--%3E%20get%0A%20%20%20%20pool%20--%3E%20refresh%0A%20%20%20%20mixin%20--%3E%20refresh%0A%20%20%20%20mixin%20--%3E%20Client%0A%20%20%20%20request%20--%3E%20mixin%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_6-2-登录流程" tabindex="-1">6.2 登录流程 <a class="header-anchor" href="#_6-2-登录流程" aria-label="Permalink to &quot;6.2 登录流程&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-394",
        class: "mermaid",
        graph: "flowchart%20TB%0A%20%20%20%20Start(%5B%E5%BC%80%E5%A7%8B%E7%99%BB%E5%BD%95%5D)%20--%3E%20CheckType%7B%E7%99%BB%E5%BD%95%E7%B1%BB%E5%9E%8B%3F%7D%0A%0A%20%20%20%20CheckType%20--%3E%7Cqrcode%7C%20QR%5B%E6%98%BE%E7%A4%BA%E4%BA%8C%E7%BB%B4%E7%A0%81%5D%0A%20%20%20%20QR%20--%3E%20WaitScan%5B%E7%AD%89%E5%BE%85%E6%89%AB%E6%8F%8F%5D%0A%20%20%20%20WaitScan%20--%3E%20CheckQR%7B%E6%89%AB%E6%8F%8F%E6%88%90%E5%8A%9F%3F%7D%0A%20%20%20%20CheckQR%20--%3E%7C%E6%98%AF%7C%20SaveCookie%5B%E4%BF%9D%E5%AD%98Cookie%5D%0A%20%20%20%20CheckQR%20--%3E%7C%E5%90%A6%7C%20WaitScan%0A%0A%20%20%20%20CheckType%20--%3E%7Cphone%7C%20Phone%5B%E8%BE%93%E5%85%A5%E6%89%8B%E6%9C%BA%E5%8F%B7%5D%0A%20%20%20%20Phone%20--%3E%20SendCode%5B%E5%8F%91%E9%80%81%E9%AA%8C%E8%AF%81%E7%A0%81%5D%0A%20%20%20%20SendCode%20--%3E%20Slider%7B%E9%9C%80%E8%A6%81%E6%BB%91%E5%9D%97%3F%7D%0A%20%20%20%20Slider%20--%3E%7C%E6%98%AF%7C%20DoSlider%5B%E6%BB%91%E5%8A%A8%E9%AA%8C%E8%AF%81%5D%0A%20%20%20%20DoSlider%20--%3E%20InputCode%5B%E8%BE%93%E5%85%A5%E9%AA%8C%E8%AF%81%E7%A0%81%5D%0A%20%20%20%20Slider%20--%3E%7C%E5%90%A6%7C%20InputCode%0A%20%20%20%20InputCode%20--%3E%20Verify%5B%E9%AA%8C%E8%AF%81%E7%99%BB%E5%BD%95%5D%0A%20%20%20%20Verify%20--%3E%20SaveCookie%0A%0A%20%20%20%20CheckType%20--%3E%7Ccookie%7C%20LoadCookie%5B%E5%8A%A0%E8%BD%BD%E5%B7%B2%E4%BF%9D%E5%AD%98Cookie%5D%0A%20%20%20%20LoadCookie%20--%3E%20VerifyCookie%7BCookie%E6%9C%89%E6%95%88%3F%7D%0A%20%20%20%20VerifyCookie%20--%3E%7C%E6%98%AF%7C%20SaveCookie%0A%20%20%20%20VerifyCookie%20--%3E%7C%E5%90%A6%7C%20Fail%5B%E7%99%BB%E5%BD%95%E5%A4%B1%E8%B4%A5%5D%0A%0A%20%20%20%20SaveCookie%20--%3E%20UpdateContext%5B%E6%9B%B4%E6%96%B0%E6%B5%8F%E8%A7%88%E5%99%A8%E4%B8%8A%E4%B8%8B%E6%96%87%5D%0A%20%20%20%20UpdateContext%20--%3E%20End(%5B%E7%99%BB%E5%BD%95%E5%AE%8C%E6%88%90%5D)%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_6-3-浏览器管理" tabindex="-1">6.3 浏览器管理 <a class="header-anchor" href="#_6-3-浏览器管理" aria-label="Permalink to &quot;6.3 浏览器管理&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-398",
        class: "mermaid",
        graph: "flowchart%20LR%0A%20%20%20%20subgraph%20Mode%5B%22%E5%90%AF%E5%8A%A8%E6%A8%A1%E5%BC%8F%22%5D%0A%20%20%20%20%20%20%20%20standard%5B%22%E6%A0%87%E5%87%86%E6%A8%A1%E5%BC%8F%3Cbr%2F%3EPlaywright%22%5D%0A%20%20%20%20%20%20%20%20cdp%5B%22CDP%E6%A8%A1%E5%BC%8F%3Cbr%2F%3EChrome%20DevTools%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Standard%5B%22%E6%A0%87%E5%87%86%E6%A8%A1%E5%BC%8F%E6%B5%81%E7%A8%8B%22%5D%0A%20%20%20%20%20%20%20%20launch%5B%22chromium.launch()%22%5D%0A%20%20%20%20%20%20%20%20context%5B%22new_context()%22%5D%0A%20%20%20%20%20%20%20%20stealth%5B%22%E6%B3%A8%E5%85%A5stealth.js%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20CDP%5B%22CDP%E6%A8%A1%E5%BC%8F%E6%B5%81%E7%A8%8B%22%5D%0A%20%20%20%20%20%20%20%20detect%5B%22%E6%A3%80%E6%B5%8B%E6%B5%8F%E8%A7%88%E5%99%A8%E8%B7%AF%E5%BE%84%22%5D%0A%20%20%20%20%20%20%20%20start%5B%22%E5%90%AF%E5%8A%A8%E6%B5%8F%E8%A7%88%E5%99%A8%E8%BF%9B%E7%A8%8B%22%5D%0A%20%20%20%20%20%20%20%20connect%5B%22connect_over_cdp()%22%5D%0A%20%20%20%20%20%20%20%20cdpContext%5B%22%E8%8E%B7%E5%8F%96%E5%B7%B2%E6%9C%89%E4%B8%8A%E4%B8%8B%E6%96%87%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Features%5B%22%E7%89%B9%E6%80%A7%22%5D%0A%20%20%20%20%20%20%20%20f1%5B%22%E7%94%A8%E6%88%B7%E6%95%B0%E6%8D%AE%E6%8C%81%E4%B9%85%E5%8C%96%22%5D%0A%20%20%20%20%20%20%20%20f2%5B%22%E6%89%A9%E5%B1%95%E5%92%8C%E8%AE%BE%E7%BD%AE%E7%BB%A7%E6%89%BF%22%5D%0A%20%20%20%20%20%20%20%20f3%5B%22%E5%8F%8D%E6%A3%80%E6%B5%8B%E8%83%BD%E5%8A%9B%E5%A2%9E%E5%BC%BA%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20standard%20--%3E%20Standard%0A%20%20%20%20cdp%20--%3E%20CDP%0A%20%20%20%20CDP%20--%3E%20Features%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_6-4-缓存系统" tabindex="-1">6.4 缓存系统 <a class="header-anchor" href="#_6-4-缓存系统" aria-label="Permalink to &quot;6.4 缓存系统&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-402",
        class: "mermaid",
        graph: "classDiagram%0A%20%20%20%20class%20AbstractCache%20%7B%0A%20%20%20%20%20%20%20%20%3C%3Cabstract%3E%3E%0A%20%20%20%20%20%20%20%20%2Bget(key)*%20%E8%8E%B7%E5%8F%96%E7%BC%93%E5%AD%98%0A%20%20%20%20%20%20%20%20%2Bset(key%2C%20value%2C%20expire)*%20%E8%AE%BE%E7%BD%AE%E7%BC%93%E5%AD%98%0A%20%20%20%20%20%20%20%20%2Bkeys(pattern)*%20%E8%8E%B7%E5%8F%96%E6%89%80%E6%9C%89%E9%94%AE%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20ExpiringLocalCache%20%7B%0A%20%20%20%20%20%20%20%20-_cache%3A%20Dict%0A%20%20%20%20%20%20%20%20-_expire_times%3A%20Dict%0A%20%20%20%20%20%20%20%20%2Bget(key)%0A%20%20%20%20%20%20%20%20%2Bset(key%2C%20value%2C%20expire_time)%0A%20%20%20%20%20%20%20%20%2Bkeys(pattern)%0A%20%20%20%20%20%20%20%20-_is_expired(key)%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20RedisCache%20%7B%0A%20%20%20%20%20%20%20%20-_client%3A%20Redis%0A%20%20%20%20%20%20%20%20%2Bget(key)%0A%20%20%20%20%20%20%20%20%2Bset(key%2C%20value%2C%20expire_time)%0A%20%20%20%20%20%20%20%20%2Bkeys(pattern)%0A%20%20%20%20%7D%0A%0A%20%20%20%20class%20CacheFactory%20%7B%0A%20%20%20%20%20%20%20%20%2Bcreate_cache(type)%20AbstractCache%0A%20%20%20%20%7D%0A%0A%20%20%20%20AbstractCache%20%3C%7C--%20ExpiringLocalCache%0A%20%20%20%20AbstractCache%20%3C%7C--%20RedisCache%0A%20%20%20%20CacheFactory%20--%3E%20AbstractCache%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<hr><h2 id="_7-数据模型" tabindex="-1">7. 数据模型 <a class="header-anchor" href="#_7-数据模型" aria-label="Permalink to &quot;7. 数据模型&quot;">​</a></h2><h3 id="_7-1-orm模型关系" tabindex="-1">7.1 ORM模型关系 <a class="header-anchor" href="#_7-1-orm模型关系" aria-label="Permalink to &quot;7.1 ORM模型关系&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-410",
        class: "mermaid",
        graph: "erDiagram%0A%20%20%20%20DouyinAweme%20%7B%0A%20%20%20%20%20%20%20%20int%20id%20PK%0A%20%20%20%20%20%20%20%20string%20aweme_id%20UK%0A%20%20%20%20%20%20%20%20string%20aweme_type%0A%20%20%20%20%20%20%20%20string%20title%0A%20%20%20%20%20%20%20%20string%20desc%0A%20%20%20%20%20%20%20%20int%20create_time%0A%20%20%20%20%20%20%20%20int%20liked_count%0A%20%20%20%20%20%20%20%20int%20collected_count%0A%20%20%20%20%20%20%20%20int%20comment_count%0A%20%20%20%20%20%20%20%20int%20share_count%0A%20%20%20%20%20%20%20%20string%20user_id%20FK%0A%20%20%20%20%20%20%20%20datetime%20add_ts%0A%20%20%20%20%20%20%20%20datetime%20last_modify_ts%0A%20%20%20%20%7D%0A%0A%20%20%20%20DouyinAwemeComment%20%7B%0A%20%20%20%20%20%20%20%20int%20id%20PK%0A%20%20%20%20%20%20%20%20string%20comment_id%20UK%0A%20%20%20%20%20%20%20%20string%20aweme_id%20FK%0A%20%20%20%20%20%20%20%20string%20content%0A%20%20%20%20%20%20%20%20int%20create_time%0A%20%20%20%20%20%20%20%20int%20sub_comment_count%0A%20%20%20%20%20%20%20%20string%20user_id%0A%20%20%20%20%20%20%20%20datetime%20add_ts%0A%20%20%20%20%20%20%20%20datetime%20last_modify_ts%0A%20%20%20%20%7D%0A%0A%20%20%20%20DyCreator%20%7B%0A%20%20%20%20%20%20%20%20int%20id%20PK%0A%20%20%20%20%20%20%20%20string%20user_id%20UK%0A%20%20%20%20%20%20%20%20string%20nickname%0A%20%20%20%20%20%20%20%20string%20avatar%0A%20%20%20%20%20%20%20%20string%20desc%0A%20%20%20%20%20%20%20%20int%20follower_count%0A%20%20%20%20%20%20%20%20int%20total_favorited%0A%20%20%20%20%20%20%20%20datetime%20add_ts%0A%20%20%20%20%20%20%20%20datetime%20last_modify_ts%0A%20%20%20%20%7D%0A%0A%20%20%20%20DouyinAweme%20%7C%7C--o%7B%20DouyinAwemeComment%20%3A%20%22has%22%0A%20%20%20%20DyCreator%20%7C%7C--o%7B%20DouyinAweme%20%3A%20%22creates%22%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<h3 id="_7-2-各平台数据表" tabindex="-1">7.2 各平台数据表 <a class="header-anchor" href="#_7-2-各平台数据表" aria-label="Permalink to &quot;7.2 各平台数据表&quot;">​</a></h3><table tabindex="0"><thead><tr><th>平台</th><th>内容表</th><th>评论表</th><th>创作者表</th></tr></thead><tbody><tr><td>抖音</td><td>DouyinAweme</td><td>DouyinAwemeComment</td><td>DyCreator</td></tr><tr><td>小红书</td><td>XHSNote</td><td>XHSNoteComment</td><td>XHSCreator</td></tr><tr><td>快手</td><td>KuaishouVideo</td><td>KuaishouVideoComment</td><td>KsCreator</td></tr><tr><td>B站</td><td>BilibiliVideo</td><td>BilibiliVideoComment</td><td>BilibiliUpInfo</td></tr><tr><td>微博</td><td>WeiboNote</td><td>WeiboNoteComment</td><td>WeiboCreator</td></tr><tr><td>贴吧</td><td>TiebaNote</td><td>TiebaNoteComment</td><td>-</td></tr><tr><td>知乎</td><td>ZhihuContent</td><td>ZhihuContentComment</td><td>ZhihuCreator</td></tr></tbody></table><hr><h2 id="_8-配置系统" tabindex="-1">8. 配置系统 <a class="header-anchor" href="#_8-配置系统" aria-label="Permalink to &quot;8. 配置系统&quot;">​</a></h2><h3 id="_8-1-核心配置项" tabindex="-1">8.1 核心配置项 <a class="header-anchor" href="#_8-1-核心配置项" aria-label="Permalink to &quot;8.1 核心配置项&quot;">​</a></h3><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># config/base_config.py</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 平台选择</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">PLATFORM</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;xhs&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}">  # xhs, dy, ks, bili, wb, tieba, zhihu</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 登录配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">LOGIN_TYPE</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;qrcode&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}">  # qrcode, phone, cookie</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">SAVE_LOGIN_STATE</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> True</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 爬虫配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">CRAWLER_TYPE</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;search&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}">  # search, detail, creator</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">KEYWORDS</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;编程副业,编程兼职&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">CRAWLER_MAX_NOTES_COUNT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 15</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MAX_CONCURRENCY_NUM</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 1</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 评论配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">ENABLE_GET_COMMENTS</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> True</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">ENABLE_GET_SUB_COMMENTS</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> False</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 10</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 浏览器配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">HEADLESS</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> False</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">ENABLE_CDP_MODE</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> True</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">CDP_DEBUG_PORT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 9222</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 代理配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">ENABLE_IP_PROXY</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> False</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">IP_PROXY_PROVIDER</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;kuaidaili&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">IP_PROXY_POOL_COUNT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 2</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 存储配置</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">SAVE_DATA_OPTION</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;jsonl&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}">  # csv, db, json, jsonl, sqlite, mongodb, excel, postgres</span></span></code></pre></div><h3 id="_8-2-数据库配置" tabindex="-1">8.2 数据库配置 <a class="header-anchor" href="#_8-2-数据库配置" aria-label="Permalink to &quot;8.2 数据库配置&quot;">​</a></h3><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># config/db_config.py</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># MySQL</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MYSQL_DB_HOST</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;localhost&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MYSQL_DB_PORT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 3306</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MYSQL_DB_NAME</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;media_crawler&quot;</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># Redis</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">REDIS_DB_HOST</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;127.0.0.1&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">REDIS_DB_PORT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 6379</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># MongoDB</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MONGODB_HOST</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;localhost&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">MONGODB_PORT</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> 27017</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># SQLite</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}">SQLITE_DB_PATH</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}"> =</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> &quot;database/sqlite_tables.db&quot;</span></span></code></pre></div><hr><h2 id="_9-工具模块" tabindex="-1">9. 工具模块 <a class="header-anchor" href="#_9-工具模块" aria-label="Permalink to &quot;9. 工具模块&quot;">​</a></h2><h3 id="_9-1-工具函数概览" tabindex="-1">9.1 工具函数概览 <a class="header-anchor" href="#_9-1-工具函数概览" aria-label="Permalink to &quot;9.1 工具函数概览&quot;">​</a></h3><table tabindex="0"><thead><tr><th>模块</th><th>文件</th><th>主要功能</th></tr></thead><tbody><tr><td>应用运行器</td><td><code>app_runner.py</code></td><td>信号处理、优雅退出、清理管理</td></tr><tr><td>浏览器启动</td><td><code>browser_launcher.py</code></td><td>检测浏览器路径、启动浏览器进程</td></tr><tr><td>CDP管理</td><td><code>cdp_browser.py</code></td><td>CDP连接、浏览器上下文管理</td></tr><tr><td>爬虫工具</td><td><code>crawler_util.py</code></td><td>二维码识别、验证码处理、User-Agent</td></tr><tr><td>文件写入</td><td><code>async_file_writer.py</code></td><td>异步CSV/JSON写入、词云生成</td></tr><tr><td>滑块验证</td><td><code>slider_util.py</code></td><td>滑动验证码破解</td></tr><tr><td>时间工具</td><td><code>time_util.py</code></td><td>时间戳转换、日期处理</td></tr></tbody></table><h3 id="_9-2-应用运行管理" tabindex="-1">9.2 应用运行管理 <a class="header-anchor" href="#_9-2-应用运行管理" aria-label="Permalink to &quot;9.2 应用运行管理&quot;">​</a></h3>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-648",
        class: "mermaid",
        graph: "flowchart%20TB%0A%20%20%20%20Start(%5B%E7%A8%8B%E5%BA%8F%E5%90%AF%E5%8A%A8%5D)%20--%3E%20Run%5B%22run(app_main%2C%20app_cleanup)%22%5D%0A%20%20%20%20Run%20--%3E%20Main%5B%22%E6%89%A7%E8%A1%8C%20app_main()%22%5D%0A%20%20%20%20Main%20--%3E%20Running%7B%E8%BF%90%E8%A1%8C%E4%B8%AD%7D%0A%0A%20%20%20%20Running%20--%3E%7C%E6%AD%A3%E5%B8%B8%E5%AE%8C%E6%88%90%7C%20Cleanup1%5B%22%E6%89%A7%E8%A1%8C%20app_cleanup()%22%5D%0A%20%20%20%20Running%20--%3E%7CSIGINT%2FSIGTERM%7C%20Signal%5B%22%E6%8D%95%E8%8E%B7%E4%BF%A1%E5%8F%B7%22%5D%0A%0A%20%20%20%20Signal%20--%3E%20First%7B%E7%AC%AC%E4%B8%80%E6%AC%A1%E4%BF%A1%E5%8F%B7%3F%7D%0A%20%20%20%20First%20--%3E%7C%E6%98%AF%7C%20Cleanup2%5B%22%E5%90%AF%E5%8A%A8%E6%B8%85%E7%90%86%E6%B5%81%E7%A8%8B%22%5D%0A%20%20%20%20First%20--%3E%7C%E5%90%A6%7C%20Force%5B%22%E5%BC%BA%E5%88%B6%E9%80%80%E5%87%BA%22%5D%0A%0A%20%20%20%20Cleanup1%20%26%20Cleanup2%20--%3E%20Cancel%5B%22%E5%8F%96%E6%B6%88%E5%85%B6%E4%BB%96%E4%BB%BB%E5%8A%A1%22%5D%0A%20%20%20%20Cancel%20--%3E%20Wait%5B%22%E7%AD%89%E5%BE%85%E4%BB%BB%E5%8A%A1%E5%AE%8C%E6%88%90%3Cbr%2F%3E(%E8%B6%85%E6%97%B615%E7%A7%92)%22%5D%0A%20%20%20%20Wait%20--%3E%20End(%5B%E7%A8%8B%E5%BA%8F%E9%80%80%E5%87%BA%5D)%0A%20%20%20%20Force%20--%3E%20End%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<hr><h2 id="_10-模块依赖关系" tabindex="-1">10. 模块依赖关系 <a class="header-anchor" href="#_10-模块依赖关系" aria-label="Permalink to &quot;10. 模块依赖关系&quot;">​</a></h2>`);
  ssrRenderSuspense(_push, {
    default: () => {
      _push(ssrRenderComponent(_component_Mermaid, {
        id: "mermaid-653",
        class: "mermaid",
        graph: "flowchart%20TB%0A%20%20%20%20subgraph%20Entry%5B%22%E5%85%A5%E5%8F%A3%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20main%5B%22main.py%22%5D%0A%20%20%20%20%20%20%20%20config%5B%22config%2F%22%5D%0A%20%20%20%20%20%20%20%20cmdarg%5B%22cmd_arg%2F%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Core%5B%22%E6%A0%B8%E5%BF%83%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20base%5B%22base%2Fbase_crawler.py%22%5D%0A%20%20%20%20%20%20%20%20platforms%5B%22media_platform%2F*%2F%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Client%5B%22%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20client%5B%22*%2Fclient.py%22%5D%0A%20%20%20%20%20%20%20%20login%5B%22*%2Flogin.py%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Storage%5B%22%E5%AD%98%E5%82%A8%E5%B1%82%22%5D%0A%20%20%20%20%20%20%20%20store%5B%22store%2F%22%5D%0A%20%20%20%20%20%20%20%20database%5B%22database%2F%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20Infra%5B%22%E5%9F%BA%E7%A1%80%E8%AE%BE%E6%96%BD%22%5D%0A%20%20%20%20%20%20%20%20proxy%5B%22proxy%2F%22%5D%0A%20%20%20%20%20%20%20%20cache%5B%22cache%2F%22%5D%0A%20%20%20%20%20%20%20%20tools%5B%22tools%2F%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20subgraph%20External%5B%22%E5%A4%96%E9%83%A8%E4%BE%9D%E8%B5%96%22%5D%0A%20%20%20%20%20%20%20%20playwright%5B%22Playwright%22%5D%0A%20%20%20%20%20%20%20%20httpx%5B%22httpx%22%5D%0A%20%20%20%20%20%20%20%20sqlalchemy%5B%22SQLAlchemy%22%5D%0A%20%20%20%20%20%20%20%20motor%5B%22Motor%2FMongoDB%22%5D%0A%20%20%20%20end%0A%0A%20%20%20%20main%20--%3E%20config%0A%20%20%20%20main%20--%3E%20cmdarg%0A%20%20%20%20main%20--%3E%20Core%0A%0A%20%20%20%20Core%20--%3E%20base%0A%20%20%20%20platforms%20--%3E%20base%0A%20%20%20%20platforms%20--%3E%20Client%0A%0A%20%20%20%20client%20--%3E%20proxy%0A%20%20%20%20client%20--%3E%20httpx%0A%20%20%20%20login%20--%3E%20tools%0A%0A%20%20%20%20platforms%20--%3E%20Storage%0A%20%20%20%20Storage%20--%3E%20sqlalchemy%0A%20%20%20%20Storage%20--%3E%20motor%0A%0A%20%20%20%20client%20--%3E%20playwright%0A%20%20%20%20tools%20--%3E%20playwright%0A%0A%20%20%20%20proxy%20--%3E%20cache%0A"
      }, null, _parent));
    },
    fallback: () => {
      _push(` Loading... `);
    },
    _: 1
  });
  _push(`<hr><h2 id="_11-扩展指南" tabindex="-1">11. 扩展指南 <a class="header-anchor" href="#_11-扩展指南" aria-label="Permalink to &quot;11. 扩展指南&quot;">​</a></h2><h3 id="_11-1-添加新平台" tabindex="-1">11.1 添加新平台 <a class="header-anchor" href="#_11-1-添加新平台" aria-label="Permalink to &quot;11.1 添加新平台&quot;">​</a></h3><ol><li>在 <code>media_platform/</code> 下创建新目录</li><li>实现以下核心文件： <ul><li><code>core.py</code> - 继承 <code>AbstractCrawler</code></li><li><code>client.py</code> - 继承 <code>AbstractApiClient</code> 和 <code>ProxyRefreshMixin</code></li><li><code>login.py</code> - 继承 <code>AbstractLogin</code></li><li><code>field.py</code> - 定义平台枚举</li></ul></li><li>在 <code>store/</code> 下创建对应存储目录</li><li>在 <code>main.py</code> 的 <code>CrawlerFactory.CRAWLERS</code> 中注册</li></ol><h3 id="_11-2-添加新存储方式" tabindex="-1">11.2 添加新存储方式 <a class="header-anchor" href="#_11-2-添加新存储方式" aria-label="Permalink to &quot;11.2 添加新存储方式&quot;">​</a></h3><ol><li>在 <code>store/</code> 下创建新的存储实现类</li><li>继承 <code>AbstractStore</code> 基类</li><li>实现 <code>store_content</code>、<code>store_comment</code>、<code>store_creator</code> 方法</li><li>在各平台的 <code>StoreFactory.STORES</code> 中注册</li></ol><h3 id="_11-3-添加新代理提供商" tabindex="-1">11.3 添加新代理提供商 <a class="header-anchor" href="#_11-3-添加新代理提供商" aria-label="Permalink to &quot;11.3 添加新代理提供商&quot;">​</a></h3><ol><li>在 <code>proxy/providers/</code> 下创建新的代理类</li><li>继承 <code>BaseProxy</code> 基类</li><li>实现 <code>get_proxy()</code> 方法</li><li>在配置中注册</li></ol><hr><h2 id="_12-快速参考" tabindex="-1">12. 快速参考 <a class="header-anchor" href="#_12-快速参考" aria-label="Permalink to &quot;12. 快速参考&quot;">​</a></h2><h3 id="_12-1-常用命令" tabindex="-1">12.1 常用命令 <a class="header-anchor" href="#_12-1-常用命令" aria-label="Permalink to &quot;12.1 常用命令&quot;">​</a></h3><div class="language-bash vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">bash</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 启动爬虫</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}">python</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> main.py</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 指定平台</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}">python</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> main.py</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> --platform</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> xhs</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 指定登录方式</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}">python</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> main.py</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> --lt</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> qrcode</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 指定爬虫类型</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}">python</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> main.py</span><span style="${ssrRenderStyle({ "--shiki-light": "#005CC5", "--shiki-dark": "#79B8FF" })}"> --type</span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}"> search</span></span></code></pre></div><h3 id="_12-2-关键文件路径" tabindex="-1">12.2 关键文件路径 <a class="header-anchor" href="#_12-2-关键文件路径" aria-label="Permalink to &quot;12.2 关键文件路径&quot;">​</a></h3><table tabindex="0"><thead><tr><th>用途</th><th>文件路径</th></tr></thead><tbody><tr><td>程序入口</td><td><code>main.py</code></td></tr><tr><td>核心配置</td><td><code>config/base_config.py</code></td></tr><tr><td>数据库配置</td><td><code>config/db_config.py</code></td></tr><tr><td>爬虫基类</td><td><code>base/base_crawler.py</code></td></tr><tr><td>ORM模型</td><td><code>database/models.py</code></td></tr><tr><td>代理池</td><td><code>proxy/proxy_ip_pool.py</code></td></tr><tr><td>CDP浏览器</td><td><code>tools/cdp_browser.py</code></td></tr></tbody></table><hr><p><em>文档生成时间: 2025-12-18</em></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("项目架构文档.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ______ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  ______ as default
};
