define(function(require) {
  var U = require('utils');

  describe('Testing utils module:', function() {
    describe('degToRad', function() {
      it('should convert degrees to radians properly.', function() {
        expect(U.degToRad(180)).toEqual(Math.PI);
      });
    });

    describe('radToDeg', function() {
      it('should convert radians to degrees properly.', function() {
        expect(U.radToDeg(Math.PI)).toEqual(180.0);
      });
    });
  });
});
