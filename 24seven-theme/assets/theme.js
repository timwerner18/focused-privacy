/* ==========================================================================
   24SEVEN E-Kiosk – Theme JS (Vanilla, kein Framework)
   Module: Age-Gate, Menü-Drawer, Cart-Drawer, Quick-Add, Varianten-Picker,
   Sticky-ATC, PLZ-Checker, Newsletter-Popup, Cookie-Consent, Tracking-Slots.
   ========================================================================== */
(function () {
  'use strict';

  var FREE_SHIPPING_THRESHOLD = parseInt(document.documentElement.dataset.freeShippingCents || '3900', 10);
  var EXPRESS_PLZ_PREFIXES = ['08', '09'];

  /* ---------- Helpers ---------- */
  function qs(sel, ctx) { return (ctx || document).querySelector(sel); }
  function qsa(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function formatMoney(cents) {
    return (cents / 100).toFixed(2).replace('.', ',') + ' €';
  }
  function setCookie(name, value, days) {
    var d = new Date();
    d.setTime(d.getTime() + days * 864e5);
    document.cookie = name + '=' + value + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
  }
  function getCookie(name) {
    var m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : null;
  }

  /* ---------- Age-Gate ---------- */
  function initAgeGate() {
    var gate = qs('[data-age-gate]');
    if (!gate) return;
    var isRestrictedPage = document.body.dataset.ageRestricted === 'true';
    var status = getCookie('ekiosk_age');

    if (status === 'ok') { gate.remove(); return; }
    if (status === 'denied' && !isRestrictedPage) { gate.remove(); return; }

    gate.hidden = false;
    document.documentElement.style.overflow = 'hidden';

    qs('[data-age-yes]', gate).addEventListener('click', function () {
      setCookie('ekiosk_age', 'ok', 30);
      gate.remove();
      document.documentElement.style.overflow = '';
    });
    qs('[data-age-no]', gate).addEventListener('click', function () {
      setCookie('ekiosk_age', 'denied', 1);
      var box = qs('.age-gate__box', gate);
      box.innerHTML = '<h2>Sorry!</h2><p class="text-muted">Dieser Bereich ist erst ab 18 Jahren zugänglich. Schau gern wieder vorbei, wenn du 18 bist.</p><a class="btn btn--secondary" href="/">Zur Startseite</a>';
    });
  }

  /* ---------- Menü-Drawer (mobil) ---------- */
  function initMenuDrawer() {
    var drawer = qs('[data-menu-drawer]');
    if (!drawer) return;
    var open = function () { drawer.classList.add('is-open'); drawer.setAttribute('aria-hidden', 'false'); };
    var close = function () { drawer.classList.remove('is-open'); drawer.setAttribute('aria-hidden', 'true'); };
    qsa('[data-menu-open]').forEach(function (btn) { btn.addEventListener('click', open); });
    qsa('[data-menu-close]', drawer).forEach(function (el) { el.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }

  /* ---------- Cart-Drawer ---------- */
  var CartDrawer = {
    el: null,
    init: function () {
      this.el = qs('[data-cart-drawer]');
      if (!this.el) return;
      var self = this;
      qsa('[data-cart-open]').forEach(function (btn) {
        btn.addEventListener('click', function (e) { e.preventDefault(); self.open(); });
      });
      qsa('[data-cart-close]', this.el).forEach(function (el) {
        el.addEventListener('click', function () { self.close(); });
      });
      this.el.addEventListener('click', function (e) {
        var qtyBtn = e.target.closest('[data-qty-change]');
        var removeBtn = e.target.closest('[data-line-remove]');
        var upsellBtn = e.target.closest('[data-upsell-add]');
        if (qtyBtn) self.changeQty(qtyBtn.dataset.line, parseInt(qtyBtn.dataset.qtyChange, 10));
        if (removeBtn) self.updateLine(removeBtn.dataset.line, 0);
        if (upsellBtn) self.add(upsellBtn.dataset.upsellAdd, 1);
      });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') self.close(); });
    },
    open: function () {
      this.refresh();
      this.el.classList.add('is-open');
      this.el.setAttribute('aria-hidden', 'false');
    },
    close: function () {
      this.el.classList.remove('is-open');
      this.el.setAttribute('aria-hidden', 'true');
    },
    add: function (variantId, qty, button) {
      var self = this;
      return fetch('/cart/add.js', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: parseInt(variantId, 10), quantity: qty || 1 })
      })
        .then(function (r) {
          if (!r.ok) throw new Error('add failed');
          return r.json();
        })
        .then(function () {
          if (button) {
            button.classList.add('is-added');
            var prev = button.textContent;
            button.textContent = '✓ Im Warenkorb';
            setTimeout(function () { button.classList.remove('is-added'); button.textContent = prev; }, 1800);
          }
          self.open();
        })
        .catch(function () {
          if (button) button.textContent = 'Nicht verfügbar';
        });
    },
    changeQty: function (line, delta) {
      var input = qs('[data-line-qty="' + line + '"]', this.el);
      var current = input ? parseInt(input.value, 10) : 1;
      this.updateLine(line, Math.max(0, current + delta));
    },
    updateLine: function (line, qty) {
      var self = this;
      fetch('/cart/change.js', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ line: parseInt(line, 10), quantity: qty })
      })
        .then(function (r) { return r.json(); })
        .then(function () { self.refresh(); });
    },
    refresh: function () {
      var self = this;
      fetch(window.location.pathname + '?section_id=cart-drawer')
        .then(function (r) { return r.text(); })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var fresh = qs('[data-cart-drawer-content]', doc);
          var target = qs('[data-cart-drawer-content]', self.el);
          if (fresh && target) target.innerHTML = fresh.innerHTML;
          self.updateBubble(doc);
          self.updateShippingProgress();
          initPlzChecker(self.el);
        });
    },
    updateBubble: function (doc) {
      var freshBubble = qs('[data-cart-count]', doc || document);
      var bubbles = qsa('[data-cart-count]');
      if (!freshBubble) return;
      bubbles.forEach(function (b) {
        b.textContent = freshBubble.textContent;
        b.hidden = freshBubble.textContent === '0';
      });
    },
    updateShippingProgress: function () {
      var wrap = qs('[data-shipping-progress]', this.el);
      if (!wrap) return;
      var total = parseInt(wrap.dataset.cartTotal || '0', 10);
      var remaining = FREE_SHIPPING_THRESHOLD - total;
      var fill = qs('.shipping-progress__fill', wrap);
      var label = qs('.shipping-progress__label', wrap);
      var pct = Math.min(100, Math.round((total / FREE_SHIPPING_THRESHOLD) * 100));
      if (fill) fill.style.width = pct + '%';
      if (label) {
        if (remaining > 0) {
          wrap.classList.remove('is-reached');
          label.textContent = 'Noch ' + formatMoney(remaining) + ' bis Gratisversand 🚚';
        } else {
          wrap.classList.add('is-reached');
          label.textContent = '🎉 Gratisversand freigeschaltet!';
        }
      }
    }
  };

  /* ---------- Quick-Add ---------- */
  function initQuickAdd() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-quick-add]');
      if (!btn) return;
      e.preventDefault();
      CartDrawer.add(btn.dataset.quickAdd, 1, btn);
    });
  }

  /* ---------- Produktseite: Varianten, Menge, ATC, Sticky-ATC ---------- */
  function initProductForm() {
    var form = qs('[data-product-form]');
    if (!form) return;
    var variantData = qs('[data-variant-json]');
    var variants = variantData ? JSON.parse(variantData.textContent) : [];
    var idInput = qs('[name="id"]', form);

    function currentOptions() {
      return qsa('.variant-picker input:checked', form).map(function (i) { return i.value; });
    }
    function findVariant(opts) {
      return variants.find(function (v) {
        return opts.every(function (opt, i) { return v['option' + (i + 1)] === opt; });
      });
    }
    function updatePrice(variant) {
      var priceEl = qs('[data-product-price]');
      var compareEl = qs('[data-product-compare]');
      var stickyPrice = qs('[data-sticky-price]');
      if (priceEl) priceEl.textContent = formatMoney(variant.price);
      if (stickyPrice) stickyPrice.textContent = formatMoney(variant.price);
      if (compareEl) {
        if (variant.compare_at_price > variant.price) {
          compareEl.hidden = false;
          qs('s', compareEl).textContent = formatMoney(variant.compare_at_price);
        } else {
          compareEl.hidden = true;
        }
      }
    }
    qsa('.variant-picker input', form).forEach(function (input) {
      input.addEventListener('change', function () {
        var variant = findVariant(currentOptions());
        if (!variant) return;
        idInput.value = variant.id;
        updatePrice(variant);
        var atc = qs('[data-atc]', form);
        if (atc) {
          atc.disabled = !variant.available;
          atc.textContent = variant.available ? 'In den Warenkorb' : 'Ausverkauft';
        }
      });
    });

    qsa('[data-qty-btn]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var input = qs('[name="quantity"]', form);
        var val = parseInt(input.value, 10) || 1;
        input.value = Math.max(1, val + parseInt(btn.dataset.qtyBtn, 10));
      });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var qty = parseInt(qs('[name="quantity"]', form).value, 10) || 1;
      CartDrawer.add(idInput.value, qty, qs('[data-atc]', form));
    });

    // Sticky-ATC auf Mobile: einblenden, sobald der Haupt-Button aus dem Viewport ist
    var sticky = qs('[data-sticky-atc]');
    var mainAtc = qs('[data-atc]', form);
    if (sticky && mainAtc && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        sticky.classList.toggle('is-visible', !entries[0].isIntersecting);
      }, { threshold: 0 }).observe(mainAtc);
      qs('[data-sticky-add]', sticky).addEventListener('click', function () {
        CartDrawer.add(idInput.value, 1, this);
      });
    }
  }

  /* ---------- Produkt-Galerie ---------- */
  function initGallery() {
    var main = qs('[data-gallery-main] img');
    if (!main) return;
    qsa('[data-gallery-thumb]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        main.src = btn.dataset.galleryThumb;
        qsa('[data-gallery-thumb]').forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
      });
    });
  }

  /* ---------- PLZ-Checker (Cart) ---------- */
  function initPlzChecker(ctx) {
    var checker = qs('[data-plz-checker]', ctx || document);
    if (!checker || checker.dataset.bound) return;
    checker.dataset.bound = 'true';
    var input = qs('input', checker);
    var result = qs('[data-plz-result]', checker);
    qs('button', checker).addEventListener('click', function (e) {
      e.preventDefault();
      var plz = (input.value || '').trim();
      if (!/^\d{5}$/.test(plz)) {
        result.className = 'plz-checker__result';
        result.textContent = 'Bitte gültige PLZ eingeben (5 Ziffern).';
        return;
      }
      var isExpress = EXPRESS_PLZ_PREFIXES.some(function (p) { return plz.indexOf(p) === 0; });
      if (isExpress) {
        result.className = 'plz-checker__result is-express';
        result.textContent = '⚡ Express-Region – meist in 24 h bei dir!';
      } else {
        result.className = 'plz-checker__result';
        result.textContent = '🚚 Lieferzeit: 1–3 Werktage.';
      }
    });
  }

  /* ---------- Newsletter-Popup (Exit-Intent, einmalig) ---------- */
  function initNewsletterPopup() {
    var popup = qs('[data-nl-popup]');
    if (!popup || getCookie('ekiosk_nl') || getCookie('ekiosk_age') === 'denied') return;

    function show() {
      if (getCookie('ekiosk_nl')) return;
      popup.hidden = false;
      setCookie('ekiosk_nl', 'shown', 30);
    }
    function close() { popup.hidden = true; }

    // Exit-Intent (Desktop): Maus verlässt Viewport nach oben
    document.addEventListener('mouseout', function (e) {
      if (!e.relatedTarget && e.clientY <= 0) show();
    });
    // Mobile Fallback: nach 45 s
    setTimeout(function () {
      if (window.matchMedia('(max-width: 749px)').matches) show();
    }, 45000);

    qsa('[data-nl-close]', popup).forEach(function (el) { el.addEventListener('click', close); });
  }

  /* ---------- Cookie-Consent (Shopify Customer Privacy API) ---------- */
  function initConsent() {
    var banner = qs('[data-cookie-banner]');
    if (!banner) return;

    function applyConsent(marketing, analytics) {
      if (window.Shopify && Shopify.customerPrivacy) {
        Shopify.customerPrivacy.setTrackingConsent(
          { marketing: marketing, analytics: analytics, preferences: true, sale_of_data: marketing },
          function () { loadTrackingScripts(); }
        );
      } else {
        setCookie('ekiosk_consent', marketing ? 'all' : 'essential', 365);
        if (marketing) loadTrackingScripts();
      }
      banner.hidden = true;
    }

    function needsBanner() {
      if (getCookie('ekiosk_consent')) return false;
      if (window.Shopify && Shopify.customerPrivacy && Shopify.customerPrivacy.shouldShowBanner) {
        return Shopify.customerPrivacy.shouldShowBanner();
      }
      return true;
    }

    function boot() {
      if (needsBanner()) banner.hidden = false;
      else if (hasMarketingConsent()) loadTrackingScripts();
    }

    if (window.Shopify && Shopify.loadFeatures) {
      Shopify.loadFeatures(
        [{ name: 'consent-tracking-api', version: '0.1' }],
        function (err) { if (!err) boot(); else banner.hidden = false; }
      );
    } else {
      boot();
    }

    qs('[data-consent-accept]', banner).addEventListener('click', function () {
      setCookie('ekiosk_consent', 'all', 365);
      applyConsent(true, true);
    });
    qs('[data-consent-essential]', banner).addEventListener('click', function () {
      setCookie('ekiosk_consent', 'essential', 365);
      applyConsent(false, false);
    });
  }

  function hasMarketingConsent() {
    if (window.Shopify && Shopify.customerPrivacy && Shopify.customerPrivacy.marketingAllowed) {
      return Shopify.customerPrivacy.marketingAllowed();
    }
    return getCookie('ekiosk_consent') === 'all';
  }

  /* ---------- Tracking-Slots (nur nach Consent laden) ---------- */
  function loadTrackingScripts() {
    if (window.__trackingLoaded) return;
    window.__trackingLoaded = true;
    qsa('script[type="text/plain"][data-consent="marketing"]').forEach(function (stub) {
      var s = document.createElement('script');
      if (stub.dataset.src) s.src = stub.dataset.src;
      else s.textContent = stub.textContent;
      document.head.appendChild(s);
    });
  }

  /* ---------- Boot ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    initAgeGate();
    initMenuDrawer();
    CartDrawer.init();
    initQuickAdd();
    initProductForm();
    initGallery();
    initPlzChecker();
    initNewsletterPopup();
    initConsent();
    CartDrawer.updateShippingProgress();
  });
})();
