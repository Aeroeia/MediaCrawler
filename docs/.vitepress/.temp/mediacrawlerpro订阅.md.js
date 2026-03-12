import { ssrRenderAttrs, ssrRenderAttr } from "vue/server-renderer";
import { _ as _imports_0 } from "./relakkes_weichat.DXJZ5bSI.js";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"订阅MediaCrawlerPro版本源码访问权限","description":"","frontmatter":{},"headers":[],"relativePath":"mediacrawlerpro订阅.md","filePath":"mediacrawlerpro订阅.md","lastUpdated":1760275151000}');
const _sfc_main = { name: "mediacrawlerpro订阅.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="订阅mediacrawlerpro版本源码访问权限" tabindex="-1">订阅MediaCrawlerPro版本源码访问权限 <a class="header-anchor" href="#订阅mediacrawlerpro版本源码访问权限" aria-label="Permalink to &quot;订阅MediaCrawlerPro版本源码访问权限&quot;">​</a></h1><h2 id="获取pro版本的访问权限" tabindex="-1">获取Pro版本的访问权限 <a class="header-anchor" href="#获取pro版本的访问权限" aria-label="Permalink to &quot;获取Pro版本的访问权限&quot;">​</a></h2><blockquote><p>MediaCrawler开源超过一年了，相信该仓库帮过不少朋友低门槛的学习和了解爬虫。维护真的耗费了大量精力和人力 <br></p><p>所以Pro版本不会开源，可以订阅Pro版本让我更加有动力去更新。<br></p><p>如果感兴趣可以加我微信，订阅Pro版本访问权限哦，有门槛💰。<br></p><p>仅针对想学习Pro版本源码实现的用户，如果是公司或者商业化盈利性质的就不要加我了，谢谢🙏</p><p>代码设计拓展性强，可以自己扩展更多的爬虫平台，更多的数据存储方式，相信对你架构这种爬虫代码有所帮助。</p><p><strong>MediaCrawlerPro项目主页地址</strong><a href="https://github.com/MediaCrawlerPro" target="_blank" rel="noreferrer">MediaCrawlerPro Github主页地址</a></p></blockquote><p>扫描下方我的个人微信，备注：pro版本（如果图片展示不出来，可以直接添加我的微信号：relakkes）</p><p><img${ssrRenderAttr("src", _imports_0)} alt="relakkes_weichat.JPG"></p><h2 id="pro版本诞生的背景" tabindex="-1">Pro版本诞生的背景 <a class="header-anchor" href="#pro版本诞生的背景" aria-label="Permalink to &quot;Pro版本诞生的背景&quot;">​</a></h2><p><a href="https://github.com/NanmiCoder/MediaCrawler" target="_blank" rel="noreferrer">MediaCrawler</a>这个项目开源至今获得了大量的关注，同时也暴露出来了一系列问题，比如：</p><ul><li>能否支持多账号？</li><li>能否在linux部署？</li><li>能否去掉playwright的依赖？</li><li>有没有更简单的部署方法？</li><li>有没有针对新手上门槛更低的方法？</li></ul><p>诸如上面的此类问题，想要在原有项目上去动刀，无疑是增加了复杂度，可能导致后续的维护更加困难。 出于可持续维护、简便易用、部署简单等目的，对MediaCrawler进行彻底重构。</p><h2 id="项目介绍" tabindex="-1">项目介绍 <a class="header-anchor" href="#项目介绍" aria-label="Permalink to &quot;项目介绍&quot;">​</a></h2><h3 id="mediacrawler的pro版本python实现" tabindex="-1"><a href="https://github.com/NanmiCoder/MediaCrawler" target="_blank" rel="noreferrer">MediaCrawler</a>的Pro版本python实现 <a class="header-anchor" href="#mediacrawler的pro版本python实现" aria-label="Permalink to &quot;[MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)的Pro版本python实现&quot;">​</a></h3><p><strong>小红书爬虫</strong>，<strong>抖音爬虫</strong>， <strong>快手爬虫</strong>， <strong>B站爬虫</strong>， <strong>微博爬虫</strong>，<strong>百度贴吧</strong>，<strong>知乎爬虫</strong>...。</p><p>支持多种平台的爬虫，支持多种数据的爬取，支持多种数据的存储，最重要的<strong>完美支持多账号+IP代理池，让你的爬虫更加稳定</strong>。 相较于MediaCrawler，Pro版本最大的变化：</p><ul><li>去掉了playwright的依赖，不再将Playwright集成到爬虫主干中，依赖过重。</li><li>增加了Docker，Docker-compose的方式部署，让部署更加简单。</li><li>多账号+IP代理池的支持，让爬虫更加稳定。</li><li>新增签名服务，解耦签名逻辑，让爬虫更加灵活。</li></ul></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("mediacrawlerpro订阅.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const mediacrawlerpro__ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  mediacrawlerpro__ as default
};
