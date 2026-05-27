(function() {
  let _Chart;
  Object.defineProperty(window, 'Chart', {
    get: function() { return _Chart; },
    set: function(val) {
      if (val && val.defaults) {
        val.defaults.maintainAspectRatio = false;
      }
      _Chart = val;
    },
    configurable: true
  });
})();
