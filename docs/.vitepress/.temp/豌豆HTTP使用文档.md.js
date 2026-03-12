import { ssrRenderAttrs, ssrRenderAttr, ssrRenderStyle } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const _imports_0 = "/MediaCrawler/assets/wd_http_img.D7FQC0Ln.png";
const _imports_1 = "/MediaCrawler/assets/wd_http_img_4.BGoCXhvG.png";
const _imports_2 = "/MediaCrawler/assets/wd_http_img_2.FTmYnv3d.png";
const __pageData = JSON.parse('{"title":"","description":"","frontmatter":{},"headers":[],"relativePath":"豌豆HTTP使用文档.md","filePath":"豌豆HTTP使用文档.md","lastUpdated":1753981511000}');
const _sfc_main = { name: "豌豆HTTP使用文档.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h2 id="豌豆http代理使用文档-只支持企业用户" tabindex="-1">豌豆HTTP代理使用文档 （只支持企业用户） <a class="header-anchor" href="#豌豆http代理使用文档-只支持企业用户" aria-label="Permalink to &quot;豌豆HTTP代理使用文档 （只支持企业用户）&quot;">​</a></h2><h2 id="准备代理-ip-信息" tabindex="-1">准备代理 IP 信息 <a class="header-anchor" href="#准备代理-ip-信息" aria-label="Permalink to &quot;准备代理 IP 信息&quot;">​</a></h2><p>点击 <a href="https://h.wandouip.com?invite_code=rtnifi">豌豆HTTP代理</a> 官网注册并实名认证（国内使用代理 IP 必须要实名，懂的都懂）</p><h2 id="获取-ip-代理的密钥信息-appkey" tabindex="-1">获取 IP 代理的密钥信息 appkey <a class="header-anchor" href="#获取-ip-代理的密钥信息-appkey" aria-label="Permalink to &quot;获取 IP 代理的密钥信息 appkey&quot;">​</a></h2><p>从 <a href="https://h.wandouip.com?invite_code=rtnifi">豌豆HTTP代理</a> 官网获取免费试用，如下图所示 <img${ssrRenderAttr("src", _imports_0)} alt="img.png"></p><p>选择自己需要的套餐 <img${ssrRenderAttr("src", _imports_1)} alt="img_4.png"></p><p>初始化一个豌豆HTTP代理的示例，如下代码所示，需要1个参数： app_key</p><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 文件地址： proxy/providers/wandou_http_proxy.py</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># -*- coding: utf-8 -*-</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">def</span><span style="${ssrRenderStyle({ "--shiki-light": "#6F42C1", "--shiki-dark": "#B392F0" })}"> new_wandou_http_proxy</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">() -&gt; WanDouHttpProxy:</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">    构造豌豆HTTP实例</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">    Returns:</span></span>
<span class="line"></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">    return</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}"> WanDouHttpProxy(</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#E36209", "--shiki-dark": "#FFAB70" })}">        app_key</span><span style="${ssrRenderStyle({ "--shiki-light": "#D73A49", "--shiki-dark": "#F97583" })}">=</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">os.getenv(</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">            &quot;wandou_app_key&quot;</span><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">, </span><span style="${ssrRenderStyle({ "--shiki-light": "#032F62", "--shiki-dark": "#9ECBFF" })}">&quot;你的豌豆HTTP app_key&quot;</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">        ),  </span><span style="${ssrRenderStyle({ "--shiki-light": "#6A737D", "--shiki-dark": "#6A737D" })}"># 通过环境变量的方式获取豌豆HTTP app_key</span></span>
<span class="line"><span style="${ssrRenderStyle({ "--shiki-light": "#24292E", "--shiki-dark": "#E1E4E8" })}">    )</span></span></code></pre></div><p>在个人中心的<code>开放接口</code>找到 <code>app_key</code>，如下图所示</p><p><img${ssrRenderAttr("src", _imports_2)} alt="img_2.png"></p></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("豌豆HTTP使用文档.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const __HTTP____ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  __HTTP____ as default
};
