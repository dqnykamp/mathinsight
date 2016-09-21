define(function(require) {
  var U = require('utils'),
      Tool = require('tool'),
      Checkbox = require('checkbox');

  describe('Testing checkbox module:', function() {
    describe('Checkbox', function() {
      var toolContainer, tool, checkbox, x = 10, y = 10, width = 20, height = 20;

      if ($('svg')) {
        $('svg').remove();
      }
      toolContainer = $('#daimp-tool-container');
      tool = new Tool(toolContainer.get(0));
      checkbox = new Checkbox(x, y, width, height);
      tool.add(checkbox);

      it('should have been initialized properly', function() {
        expect(checkbox.node.nodeName).toBe('g');
        expect(checkbox.node.getAttribute('pointer-events')).toBe('visible');
        expect(checkbox.node.getAttribute('transform')).toBe('translate(' + x + ',' + y + ')');
      });
    });
  });
});
