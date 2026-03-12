import { ssrRenderAttrs, ssrRenderAttr } from "vue/server-renderer";
import { _ as _imports_0 } from "./relakkes_weichat.DXJZ5bSI.js";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"关于作者","description":"","frontmatter":{},"headers":[],"relativePath":"作者介绍.md","filePath":"作者介绍.md","lastUpdated":1762358883000}');
const _sfc_main = { name: "作者介绍.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="关于作者" tabindex="-1">关于作者 <a class="header-anchor" href="#关于作者" aria-label="Permalink to &quot;关于作者&quot;">​</a></h1><blockquote><p>大家都叫我阿江，网名：程序员阿江-Relakkes，目前是一名独立开发者，专注于 AI Agent 和爬虫相关的开发工作，All in AI。</p></blockquote><ul><li><a href="https://github.com/NanmiCoder/MediaCrawler" target="_blank" rel="noreferrer">Github万星开源自媒体爬虫仓库MediaCrawler作者</a></li><li>全栈程序员，熟悉Python、Golang、JavaScript，工作中主要用Golang。</li><li>曾经主导并参与过百万级爬虫采集系统架构设计与编码</li><li>爬虫是一种技术兴趣爱好，参与爬虫有一种对抗的感觉，越难越兴奋。</li><li>目前专注于 AI Agent 领域，积极探索 AI 技术的应用与创新</li><li>如果你有 AI Agent 相关的项目需要合作，欢迎联系我，我有很多时间可以投入</li></ul><h2 id="微信联系方式" tabindex="-1">微信联系方式 <a class="header-anchor" href="#微信联系方式" aria-label="Permalink to &quot;微信联系方式&quot;">​</a></h2><p><img${ssrRenderAttr("src", _imports_0)} alt="relakkes_weichat.JPG"></p><h2 id="b站主页地址" tabindex="-1">B站主页地址 <a class="header-anchor" href="#b站主页地址" aria-label="Permalink to &quot;B站主页地址&quot;">​</a></h2><p><a href="https://space.bilibili.com/434377496" target="_blank" rel="noreferrer">https://space.bilibili.com/434377496</a></p><h2 id="抖音主页地址" tabindex="-1">抖音主页地址 <a class="header-anchor" href="#抖音主页地址" aria-label="Permalink to &quot;抖音主页地址&quot;">​</a></h2><p><a href="https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE?previous_page=app_code_link" target="_blank" rel="noreferrer">https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE?previous_page=app_code_link</a></p><h2 id="小红书主页地址" tabindex="-1">小红书主页地址 <a class="header-anchor" href="#小红书主页地址" aria-label="Permalink to &quot;小红书主页地址&quot;">​</a></h2><p><a href="https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xhsshare=CopyLink&amp;appuid=5f58bd990000000001003753&amp;apptime=1724737153" target="_blank" rel="noreferrer">https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753?xhsshare=CopyLink&amp;appuid=5f58bd990000000001003753&amp;apptime=1724737153</a></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("作者介绍.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ____ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  ____ as default
};
