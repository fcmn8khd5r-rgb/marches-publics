/* Apparition au défilement. Respecte « réduire les animations ». */
(function () {
  var doux = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (doux || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (entrees) {
    entrees.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target; io.unobserve(el);
      if (el.hasAttribute('data-frise')) {
        var ligne = el.querySelector('[data-frise-line]');
        if (ligne) ligne.style.transform = 'none';
        el.querySelectorAll('[data-frise-item]').forEach(function (it) {
          it.style.opacity = '1'; it.style.transform = 'none';
        });
      } else { el.style.opacity = '1'; el.style.transform = 'none'; }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
  document.querySelectorAll('[data-reveal]').forEach(function (el) {
    el.style.opacity = '0'; el.style.transform = 'translateY(12px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    io.observe(el);
  });
  document.querySelectorAll('[data-frise]').forEach(function (el) {
    var x = el.getAttribute('data-axis') === 'x';
    var items = el.querySelectorAll('[data-frise-item]');
    var ligne = el.querySelector('[data-frise-line]');
    var pas = 0.22;
    if (ligne) {
      ligne.style.transform = x ? 'scaleX(0)' : 'scaleY(0)';
      ligne.style.transition = 'transform ' + (items.length * pas + 0.2) + 's ease-out';
    }
    items.forEach(function (it, i) {
      it.style.opacity = '0';
      it.style.transform = x ? 'translateY(6px)' : 'translateX(-6px)';
      it.style.transition = 'opacity .4s ease ' + (i * pas) + 's, transform .4s ease ' + (i * pas) + 's';
    });
    io.observe(el);
  });
})();
