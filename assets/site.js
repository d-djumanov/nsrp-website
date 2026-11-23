// NSRP — shared behaviour: mobile menu and scroll fade-in.
(function () {
  var body = document.body;
  var toggle = document.getElementById('menuToggle');

  function setMenu(open) {
    body.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  if (toggle) {
    toggle.addEventListener('click', function () {
      setMenu(!body.classList.contains('menu-open'));
    });
    document.querySelectorAll('.mobile-menu a').forEach(function (a) {
      a.addEventListener('click', function () { setMenu(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setMenu(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 960) setMenu(false);
    });
  }

  // Fade-in is an enhancement only: content is visible unless this runs, and
  // only elements starting below the fold are hidden before they scroll in.
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Opened at an anchor (e.g. /#founders): the browser jumps after this runs,
  // so positions are unreliable — skip the fade rather than risk hiding content.
  if (window.location.hash) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.remove('pending'); io.unobserve(e.target); }
    });
  }, { threshold: 0, rootMargin: '0px 0px -20px 0px' });
  document.querySelectorAll('.reveal').forEach(function (el) {
    if (el.getBoundingClientRect().top > window.innerHeight) {
      el.classList.add('pending');
      io.observe(el);
    }
  });
})();
