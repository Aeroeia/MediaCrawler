import { ssrRenderAttrs, ssrRenderAttr } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const _imports_0 = "/MediaCrawler/assets/%E4%BB%A3%E7%90%86IP%20%E6%B5%81%E7%A8%8B%E5%9B%BE.drawio.BHiuEFJc.png";
const __pageData = JSON.parse('{"title":"代理 IP 使用说明","description":"","frontmatter":{},"headers":[],"relativePath":"代理使用.md","filePath":"代理使用.md","lastUpdated":1753981511000}');
const _sfc_main = { name: "代理使用.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="代理-ip-使用说明" tabindex="-1">代理 IP 使用说明 <a class="header-anchor" href="#代理-ip-使用说明" aria-label="Permalink to &quot;代理 IP 使用说明&quot;">​</a></h1><blockquote><p>还是得跟大家再次强调下，不要对一些自媒体平台进行大规模爬虫或其他非法行为，要踩缝纫机的哦🤣</p></blockquote><h2 id="简易的流程图" tabindex="-1">简易的流程图 <a class="header-anchor" href="#简易的流程图" aria-label="Permalink to &quot;简易的流程图&quot;">​</a></h2><p><img${ssrRenderAttr("src", _imports_0)} alt="代理 IP 使用流程图"></p><h2 id="选择一个代理ip提供商" tabindex="-1">选择一个代理IP提供商 <a class="header-anchor" href="#选择一个代理ip提供商" aria-label="Permalink to &quot;选择一个代理IP提供商&quot;">​</a></h2><h3 id="快代理" tabindex="-1">快代理 <a class="header-anchor" href="#快代理" aria-label="Permalink to &quot;快代理&quot;">​</a></h3><p><a href="./快代理使用文档.html">快代理使用文档</a></p><h3 id="豌豆http文档查看" tabindex="-1">豌豆HTTP文档查看 <a class="header-anchor" href="#豌豆http文档查看" aria-label="Permalink to &quot;豌豆HTTP文档查看&quot;">​</a></h3><p><a href="./豌豆HTTP使用文档.html">豌豆HTTP使用文档</a></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("代理使用.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const ____ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  ____ as default
};
