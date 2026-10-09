/* AI4S 观测台 · 文章分享组件
 * 在 #/read/<slug> 文章详情页标题下方注入分享栏：
 * [分享到 X] [微信扫码] [复制链接]
 * 不改动站点原有 bundle，纯 DOM 注入；样式跟随站点深色主题。
 */
(function () {
  'use strict';

  var X_ICON = 'M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z';
  var WX_ICON = 'M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.27-.027-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982zm5.852 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z';
  var LINK_ICON = 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71';

  var CSS = [
    '.ai4s-sharebar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:20px 0 6px;padding-top:18px;border-top:1px solid var(--rule)}',
    '.ai4s-share-label{font-family:var(--mono);font-size:11px;letter-spacing:.18em;color:var(--muted);margin-right:4px}',
    '.ai4s-share-btn{display:inline-flex;align-items:center;gap:7px;padding:7px 15px;border-radius:999px;border:1px solid var(--rule);background:#fff;color:var(--text);font-size:13px;font-family:var(--body);cursor:pointer;transition:all .18s ease;line-height:1.4}',
    '.ai4s-share-btn svg{width:14px;height:14px;fill:currentColor;flex:none}',
    '.ai4s-share-btn svg.stroke{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}',
    '.ai4s-share-btn:hover{transform:translateY(-1px);border-color:#b9c4c0;box-shadow:0 4px 14px rgba(11,31,42,.08)}',
    '.ai4s-share-btn.ai4s-x:hover{background:#000;border-color:#000;color:#fff}',
    '.ai4s-share-btn.ai4s-wx:hover{background:#07c160;border-color:#07c160;color:#fff}',
    '.ai4s-share-btn:active{transform:translateY(0)}',
    '.ai4s-wxmask{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(4,12,16,.72);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);opacity:0;transition:opacity .22s ease}',
    '.ai4s-wxmask.show{opacity:1}',
    '.ai4s-wxcard{position:relative;background:#0e2836;border:1px solid var(--ink-line);border-radius:14px;padding:30px 34px 26px;text-align:center;max-width:320px;box-shadow:0 24px 60px rgba(0,0,0,.5);transform:translateY(8px) scale(.98);transition:transform .22s ease}',
    '.ai4s-wxmask.show .ai4s-wxcard{transform:none}',
    '.ai4s-wxcard h4{margin:0 0 4px;font-size:16px;color:#f0f6f5;font-family:var(--han-display);font-weight:700}',
    '.ai4s-wxcard .ai4s-wxsub{margin:0 0 18px;font-size:12.5px;color:rgba(226,236,235,.55)}',
    '.ai4s-wxqr{display:inline-block;background:#fff;padding:12px;border-radius:10px;line-height:0}',
    '.ai4s-wxqr img,.ai4s-wxqr canvas{display:block;width:200px!important;height:200px!important}',
    '.ai4s-wxhint{margin:16px 0 0;font-size:12px;color:rgba(226,236,235,.5);line-height:1.7}',
    '.ai4s-wxclose{position:absolute;top:10px;right:12px;border:0;background:none;color:rgba(226,236,235,.5);font-size:22px;cursor:pointer;line-height:1;padding:4px}',
    '.ai4s-wxclose:hover{color:#fff}',
    '.ai4s-toast{position:fixed;left:50%;bottom:30px;transform:translateX(-50%) translateY(12px);z-index:10000;background:#102e3d;border:1px solid var(--ink-line);color:#eaf3f2;font-size:13.5px;padding:10px 20px;border-radius:999px;box-shadow:0 12px 30px rgba(0,0,0,.45);opacity:0;pointer-events:none;transition:all .25s ease;display:flex;align-items:center;gap:8px}',
    '.ai4s-toast.show{opacity:1;transform:translateX(-50%) translateY(0)}',
    '.ai4s-toast .ok{color:#07c160;font-weight:700}'
  ].join('\n');

  function injectCSS() {
    if (document.getElementById('ai4s-share-css')) return;
    var st = document.createElement('style');
    st.id = 'ai4s-share-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  function icon(path, stroke) {
    return '<svg viewBox="0 0 24 24" class="' + (stroke ? 'stroke' : '') + '" aria-hidden="true"><path d="' + path + '"/></svg>';
  }

  function articleInfo() {
    var m = location.hash.match(/^#\/read\/([^\/?#]+)/);
    if (!m) return null;
    var slug = decodeURIComponent(m[1]);
    var h1 = document.querySelector('.reader-article h1.reader-title');
    var title = h1 ? h1.textContent.trim() : document.title.replace(/\s*[·|]\s*AI4S.*$/, '');
    var url = location.origin + location.pathname + '#/read/' + encodeURIComponent(slug);
    return { slug: slug, title: title, url: url };
  }

  function toast(msg) {
    var t = document.querySelector('.ai4s-toast');
    if (!t) {
      t = document.createElement('div');
      t.className = 'ai4s-toast';
      document.body.appendChild(t);
    }
    t.innerHTML = '<span class="ok">✓</span><span></span>';
    t.lastChild.textContent = msg;
    requestAnimationFrame(function () { t.classList.add('show'); });
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.remove('show'); }, 2200);
  }

  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, function () { fallback(); });
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
      document.body.appendChild(ta);
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta);
      done(ok);
    }
  }

  function openWxModal(info) {
    closeWxModal();
    var mask = document.createElement('div');
    mask.className = 'ai4s-wxmask';
    mask.innerHTML =
      '<div class="ai4s-wxcard" role="dialog" aria-label="微信分享">' +
      '<button class="ai4s-wxclose" aria-label="关闭">×</button>' +
      '<h4>微信扫一扫</h4>' +
      '<p class="ai4s-wxsub">在手机上继续阅读本文</p>' +
      '<div class="ai4s-wxqr"></div>' +
      '<p class="ai4s-wxhint">打开微信扫一扫<br>即可在手机上打开，也可分享给好友</p>' +
      '</div>';
    document.body.appendChild(mask);
    var qrBox = mask.querySelector('.ai4s-wxqr');
    try {
      if (typeof QRCode !== 'undefined') {
        new QRCode(qrBox, { text: info.url, width: 200, height: 200, colorDark: '#0b1f2a', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.M });
      } else { throw new Error('no lib'); }
    } catch (e) {
      var img = document.createElement('img');
      img.alt = '文章链接二维码';
      img.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(info.url);
      qrBox.appendChild(img);
    }
    requestAnimationFrame(function () { mask.classList.add('show'); });
    mask.querySelector('.ai4s-wxclose').addEventListener('click', closeWxModal);
    mask.addEventListener('click', function (e) { if (e.target === mask) closeWxModal(); });
    document.addEventListener('keydown', escClose);
  }
  function escClose(e) { if (e.key === 'Escape') closeWxModal(); }
  function closeWxModal() {
    var mask = document.querySelector('.ai4s-wxmask');
    if (mask) mask.parentNode.removeChild(mask);
    document.removeEventListener('keydown', escClose);
  }

  function buildBar(info) {
    var bar = document.createElement('div');
    bar.className = 'ai4s-sharebar';
    bar.innerHTML =
      '<span class="ai4s-share-label">分享</span>' +
      '<button type="button" class="ai4s-share-btn ai4s-x" title="分享到 X">' + icon(X_ICON) + '<span>X</span></button>' +
      '<button type="button" class="ai4s-share-btn ai4s-wx" title="微信扫码分享">' + icon(WX_ICON) + '<span>微信</span></button>' +
      '<button type="button" class="ai4s-share-btn ai4s-copy" title="复制文章链接">' + icon(LINK_ICON, true) + '<span>复制链接</span></button>';

    bar.querySelector('.ai4s-x').addEventListener('click', function () {
      var shareUrl = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(info.title) + '&url=' + encodeURIComponent(info.url);
      window.open(shareUrl, '_blank', 'noopener,width=550,height=460');
    });
    bar.querySelector('.ai4s-wx').addEventListener('click', function () { openWxModal(info); });
    bar.querySelector('.ai4s-copy').addEventListener('click', function () {
      copyText(info.url, function (ok) { toast(ok ? '链接已复制，去分享吧' : '复制失败，请手动复制地址栏'); });
    });
    return bar;
  }

  function ensureBar() {
    var info = articleInfo();
    if (!info) return;
    var article = document.querySelector('.reader-article');
    if (!article) return;
    if (article.querySelector('.ai4s-sharebar')) return;
    var h1 = article.querySelector('h1.reader-title');
    if (!h1) return;
    var anchor = article.querySelector('.reader-dek') || h1;
    anchor.after(buildBar(info));
  }

  injectCSS();
  var obs = new MutationObserver(function () { ensureBar(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('hashchange', function () { setTimeout(ensureBar, 60); });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureBar);
  } else { ensureBar(); }
})();
