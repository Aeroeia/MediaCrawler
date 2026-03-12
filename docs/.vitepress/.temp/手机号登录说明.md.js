import { ssrRenderAttrs } from "vue/server-renderer";
import { useSSRContext } from "vue";
import { _ as _export_sfc } from "./plugin-vue_export-helper.1tPrXgE0.js";
const __pageData = JSON.parse('{"title":"关于手机号+验证码登录的说明","description":"","frontmatter":{},"headers":[],"relativePath":"手机号登录说明.md","filePath":"手机号登录说明.md","lastUpdated":1726736059000}');
const _sfc_main = { name: "手机号登录说明.md" };
function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<div${ssrRenderAttrs(_attrs)}><h1 id="关于手机号-验证码登录的说明" tabindex="-1">关于手机号+验证码登录的说明 <a class="header-anchor" href="#关于手机号-验证码登录的说明" aria-label="Permalink to &quot;关于手机号+验证码登录的说明&quot;">​</a></h1><blockquote><p>配置过程相当复杂，不建议采用该种方式</p></blockquote><p>当在浏览器模拟人为发起手机号登录请求时，使用短信转发软件将验证码发送至爬虫端回填，完成自动登录</p><p>准备工作：</p><ul><li>安卓机1台（IOS没去研究，理论上监控短信也是可行的）</li><li>安装短信转发软件 <a href="https://github.com/pppscn/SmsForwarder" target="_blank" rel="noreferrer">参考仓库</a></li><li>转发软件中配置WEBHOOK相关的信息，主要分为 消息模板（请查看本项目中的recv_sms_notification.py）、一个能push短信通知的API地址</li><li>push的API地址一般是需要绑定一个域名的（当然也可以是内网的IP地址），我用的是内网穿透方式，会有一个免费的域名绑定到内网的web server，内网穿透工具 <a href="https://ngrok.com/docs/" target="_blank" rel="noreferrer">ngrok</a></li><li>安装redis并设置一个密码 <a href="https://www.cnblogs.com/hunanzp/p/12304622.html" target="_blank" rel="noreferrer">redis安装</a></li><li>执行 <code>python recv_sms_notification.py</code> 等待短信转发器发送HTTP通知</li><li>执行手机号登录的爬虫程序 <code>python main.py --platform xhs --lt phone</code></li></ul><p>备注：</p><ul><li>短信转发软件会不会监控自己手机上其他短信内容？（理论上应该不会，因为<a href="https://github.com/pppscn/SmsForwarder" target="_blank" rel="noreferrer">短信转发仓库</a> star还是蛮多的）</li></ul></div>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext();
  (ssrContext.modules || (ssrContext.modules = /* @__PURE__ */ new Set())).add("手机号登录说明.md");
  return _sfc_setup ? _sfc_setup(props, ctx) : void 0;
};
const _______ = /* @__PURE__ */ _export_sfc(_sfc_main, [["ssrRender", _sfc_ssrRender]]);
export {
  __pageData,
  _______ as default
};
