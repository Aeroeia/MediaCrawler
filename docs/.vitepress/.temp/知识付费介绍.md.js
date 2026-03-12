import { ssrRenderAttrs } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"知识付费介绍","description":"","frontmatter":{},"headers":[],"relativePath":"知识付费介绍.md","filePath":"知识付费介绍.md","lastUpdated":1762358883000}');
const _sfc_main = { name: "知识付费介绍.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="知识付费介绍" tabindex="-1">知识付费介绍 <a class="header-anchor" href="#知识付费介绍" aria-label="Permalink to &quot;知识付费介绍&quot;">​</a></h1><p>开源是一种无私奉献，从MediaCrawler开源到现在有一年多，它并没有带给我多少实质性的东西，就拿收入来说，赞助费、赞赏等等全部加起来还没有之前一个月的薪水。</p><p>后面搞了MediaCrawler源码剖析课程之后，收入稍微好一点，但也是群里兄弟对我开源的支持，在此也非常感谢你们～</p><p>但是我依然坚持持续开源，从开始的xhs、dy 2个平台支持，到现在已经有<strong>7个平台</strong>支持，每一次增加一个平台其实都会耗费很大的时间去写代码和调试代码。。。。</p><p>在今天跟一个群里好朋友聊天，他说：开源开发者也要活下去。你不要不好意思做知识付费，你的劳动是有价值的。</p><p>他点醒我了，因此我把我所提供的知识付费内容放在下面，有需要的朋友可以看看～</p><h2 id="mediacrawlerpro项目源码订阅服务" tabindex="-1">MediaCrawlerPro项目源码订阅服务 <a class="header-anchor" href="#mediacrawlerpro项目源码订阅服务" aria-label="Permalink to &quot;MediaCrawlerPro项目源码订阅服务&quot;">​</a></h2><p><a href="./mediacrawlerpro订阅.html">mediacrawlerpro订阅文档说明</a></p><h2 id="mediacrawler源码剖析视频课程" tabindex="-1">MediaCrawler源码剖析视频课程 <a class="header-anchor" href="#mediacrawler源码剖析视频课程" aria-label="Permalink to &quot;MediaCrawler源码剖析视频课程&quot;">​</a></h2><p><a href="https://relakkes.feishu.cn/wiki/JUgBwdhIeiSbAwkFCLkciHdAnhh" target="_blank" rel="noreferrer">mediacrawler源码课程介绍</a></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("知识付费介绍.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ______ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  ______ as default
};
