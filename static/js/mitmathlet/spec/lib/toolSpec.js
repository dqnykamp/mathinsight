define(function(require) {
  var U = require('utils'),
      Tool = require('tool');

  describe('Testing tool module:', function() {
    describe('Tool container', function() {
      var toolContainer = $('#daimp-tool-container'),
          tool = new Tool(toolContainer.get(0)),
          svg = $('svg').get(0);

      it('should contain only one SVG element', function() {
        expect(toolContainer).toContainElement('svg');
        expect(toolContainer.children().length).toBe(1);
      });

      it('should contain an SVG element having version 1.2 and base profile tiny.', function() {
        // Doesn't work, probably because it's SVG.
        // TODO: Figure out how to get JQuery and Jasmine JQuery to work with SVG.
        // var svg = $('#daimp-tool-container > svg');
        // expect(svg).toHaveAttr('version', '1.2');
        // expect(svg).toHaveAttr('baseProfile', 'tiny');
        expect(svg.getAttribute('version')).toEqual('1.2');
        expect(svg.getAttribute('baseProfile')).toEqual('tiny');
      });

      it('should contain an SVG element having a default size of 818x575.', function() {
        expect(svg.getAttribute('width')).toEqual('818');
        expect(svg.getAttribute('height')).toEqual('575');
      });
    });
  });
});
