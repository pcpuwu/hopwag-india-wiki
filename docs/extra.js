document.addEventListener('DOMContentLoaded', function () {
  var items = Array.from(document.querySelectorAll('.ep-item'));
  var bar = document.getElementById('host-filter');
  if (!items.length || !bar) return;
  var names = new Set();
  items.forEach(function (el) {
    (el.dataset.who || '').split(',').forEach(function (n) {
      n = n.trim(); if (n) names.add(n);
    });
  });
  function show(name) {
    bar.querySelectorAll('.host-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.name === name);
    });
    items.forEach(function (el) {
      var who = (el.dataset.who || '').split(',').map(function (s) { return s.trim(); });
      el.style.display = (name === 'All' || who.indexOf(name) > -1) ? '' : 'none';
    });
  }
  function mk(name) {
    var b = document.createElement('button');
    b.className = 'host-btn'; b.textContent = name; b.dataset.name = name;
    b.onclick = function () { show(name); };
    bar.appendChild(b);
  }
  mk('All');
  Array.from(names).sort().forEach(mk);
  show('All');
});
