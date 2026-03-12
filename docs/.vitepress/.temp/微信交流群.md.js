import { ssrRenderAttrs, ssrRenderAttr } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const _imports_0 = "/MediaCrawler/assets/QIWEI.D9p_heUz.png";
const __pageData = JSON.parse('{"title":"MediaCrawler项目微信交流群","description":"","frontmatter":{},"headers":[],"relativePath":"微信交流群.md","filePath":"微信交流群.md","lastUpdated":1768796584000}');
const _sfc_main = { name: "微信交流群.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="mediacrawler项目微信交流群" tabindex="-1">MediaCrawler项目微信交流群 <a class="header-anchor" href="#mediacrawler项目微信交流群" aria-label="Permalink to &quot;MediaCrawler项目微信交流群&quot;">​</a></h1><p>👏👏👏 汇聚爬虫技术爱好者，共同学习，共同进步。</p><p>❗️❗️❗️群内禁止广告，禁止发各类违规和MediaCrawler不相关的问题</p><h2 id="加群方式" tabindex="-1">加群方式 <a class="header-anchor" href="#加群方式" aria-label="Permalink to &quot;加群方式&quot;">​</a></h2><blockquote><p>备注：github，会有拉群小助手自动拉你进群。</p><p>如果图片展示不出来或过期，可以直接添加我的微信号：relakkes，并备注github，会有拉群小助手自动拉你进群</p></blockquote><p><img${ssrRenderAttr("src", _imports_0)} alt="relakkes_wechat"></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("微信交流群.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const _____ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  _____ as default
};
