import { ssrRenderAttrs, ssrRenderAttr } from "vue/server-renderer";
import { _ as _imports_0 } from "./relakkes_weichat.DXJZ5bSI.js";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"开发者咨询","description":"","frontmatter":{},"headers":[],"relativePath":"开发者咨询.md","filePath":"开发者咨询.md","lastUpdated":1726736635000}');
const _sfc_main = { name: "开发者咨询.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="开发者咨询" tabindex="-1">开发者咨询 <a class="header-anchor" href="#开发者咨询" aria-label="Permalink to &quot;开发者咨询&quot;">​</a></h1><h2 id="咨询价格" tabindex="-1">咨询价格 <a class="header-anchor" href="#咨询价格" aria-label="Permalink to &quot;咨询价格&quot;">​</a></h2><p>提供200/小时的咨询服务，最低收费为1小时，帮你快速解决项目中遇到的问题</p><h5 id="支持的提问类别" tabindex="-1">支持的提问类别 <a class="header-anchor" href="#支持的提问类别" aria-label="Permalink to &quot;支持的提问类别&quot;">​</a></h5><ul><li>MediaCrawler项目源码解读、安装、部署、使用问题</li><li>爬虫项目开发问题</li><li>Python、Golang、JavaScript等编程问题</li><li>JS逆向问题</li><li>其他问题（职业规划、工作经验等）</li></ul><h2 id="加我微信" tabindex="-1">加我微信 <a class="header-anchor" href="#加我微信" aria-label="Permalink to &quot;加我微信&quot;">​</a></h2><blockquote><p>备注：咨服服务</p></blockquote><p><img${ssrRenderAttr("src", _imports_0)} alt="微信二维码"></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("开发者咨询.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const _____ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  _____ as default
};
