import { ssrRenderAttrs } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"项目代码结构","description":"","frontmatter":{},"headers":[],"relativePath":"项目代码结构.md","filePath":"项目代码结构.md","lastUpdated":1757265271000}');
const _sfc_main = { name: "项目代码结构.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="项目代码结构" tabindex="-1">项目代码结构 <a class="header-anchor" href="#项目代码结构" aria-label="Permalink to &quot;项目代码结构&quot;">​</a></h1><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>MediaCrawler</span></span>
<span class="line"><span>├── base</span></span>
<span class="line"><span>│   └── base_crawler.py         # 项目的抽象基类</span></span>
<span class="line"><span>├── cache</span></span>
<span class="line"><span>│   ├── abs_cache.py            # 缓存抽象基类</span></span>
<span class="line"><span>│   ├── cache_factory.py        # 缓存工厂</span></span>
<span class="line"><span>│   ├── local_cache.py          # 本地缓存实现</span></span>
<span class="line"><span>│   └── redis_cache.py          # Redis缓存实现</span></span>
<span class="line"><span>├── cmd_arg</span></span>
<span class="line"><span>│   └── arg.py                  # 命令行参数定义</span></span>
<span class="line"><span>├── config</span></span>
<span class="line"><span>│   ├── base_config.py          # 基础配置</span></span>
<span class="line"><span>│   ├── db_config.py            # 数据库配置</span></span>
<span class="line"><span>│   └── ...                     # 各平台配置文件</span></span>
<span class="line"><span>├── constant</span></span>
<span class="line"><span>│   └── ...                     # 各平台常量定义</span></span>
<span class="line"><span>├── database</span></span>
<span class="line"><span>│   ├── db.py                   # 数据库ORM，封装增删改查</span></span>
<span class="line"><span>│   ├── db_session.py           # 数据库会话管理</span></span>
<span class="line"><span>│   └── models.py               # 数据库模型定义</span></span>
<span class="line"><span>├── docs</span></span>
<span class="line"><span>│   └── ...                     # 项目文档</span></span>
<span class="line"><span>├── libs</span></span>
<span class="line"><span>│   ├── douyin.js               # 抖音Sign函数</span></span>
<span class="line"><span>│   ├── stealth.min.js          # 去除浏览器自动化特征的JS</span></span>
<span class="line"><span>│   └── zhihu.js                # 知乎Sign函数</span></span>
<span class="line"><span>├── media_platform</span></span>
<span class="line"><span>│   ├── bilibili                # B站采集实现</span></span>
<span class="line"><span>│   ├── douyin                  # 抖音采集实现</span></span>
<span class="line"><span>│   ├── kuaishou                # 快手采集实现</span></span>
<span class="line"><span>│   ├── tieba                   # 百度贴吧采集实现</span></span>
<span class="line"><span>│   ├── weibo                   # 微博采集实现</span></span>
<span class="line"><span>│   ├── xhs                     # 小红书采集实现</span></span>
<span class="line"><span>│   └── zhihu                   # 知乎采集实现</span></span>
<span class="line"><span>├── model</span></span>
<span class="line"><span>│   ├── m_baidu_tieba.py        # 百度贴吧数据模型</span></span>
<span class="line"><span>│   ├── m_douyin.py             # 抖音数据模型</span></span>
<span class="line"><span>│   ├── m_kuaishou.py           # 快手数据模型</span></span>
<span class="line"><span>│   ├── m_weibo.py              # 微博数据模型</span></span>
<span class="line"><span>│   ├── m_xiaohongshu.py        # 小红书数据模型</span></span>
<span class="line"><span>│   └── m_zhihu.py              # 知乎数据模型</span></span>
<span class="line"><span>├── proxy</span></span>
<span class="line"><span>│   ├── base_proxy.py           # 代理基类</span></span>
<span class="line"><span>│   ├── providers               # 代理提供商实现</span></span>
<span class="line"><span>│   ├── proxy_ip_pool.py        # 代理IP池</span></span>
<span class="line"><span>│   └── types.py                # 代理类型定义</span></span>
<span class="line"><span>├── store</span></span>
<span class="line"><span>│   ├── bilibili                # B站数据存储实现</span></span>
<span class="line"><span>│   ├── douyin                  # 抖音数据存储实现</span></span>
<span class="line"><span>│   ├── kuaishou                # 快手数据存储实现</span></span>
<span class="line"><span>│   ├── tieba                   # 贴吧数据存储实现</span></span>
<span class="line"><span>│   ├── weibo                   # 微博数据存储实现</span></span>
<span class="line"><span>│   ├── xhs                     # 小红书数据存储实现</span></span>
<span class="line"><span>│   └── zhihu                   # 知乎数据存储实现</span></span>
<span class="line"><span>├── test</span></span>
<span class="line"><span>│   ├── test_db_sync.py         # 数据库同步测试</span></span>
<span class="line"><span>│   ├── test_proxy_ip_pool.py   # 代理IP池测试</span></span>
<span class="line"><span>│   └── ...                     # 其他测试用例</span></span>
<span class="line"><span>├── tools</span></span>
<span class="line"><span>│   ├── browser_launcher.py     # 浏览器启动器</span></span>
<span class="line"><span>│   ├── cdp_browser.py          # CDP浏览器控制</span></span>
<span class="line"><span>│   ├── crawler_util.py         # 爬虫工具函数</span></span>
<span class="line"><span>│   ├── utils.py                # 通用工具函数</span></span>
<span class="line"><span>│   └── ...</span></span>
<span class="line"><span>├── main.py                     # 程序入口, 支持 --init_db 参数来初始化数据库</span></span>
<span class="line"><span>├── recv_sms.py                 # 短信转发HTTP SERVER接口</span></span>
<span class="line"><span>└── var.py                      # 全局上下文变量定义</span></span></code></pre></div></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("项目代码结构.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ______ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  ______ as default
};
