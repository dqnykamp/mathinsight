MathJax.Hub.Config({
  TeX: {
    Macros: {

	//symbol for differential in vector-valued line integral
	lineIntegralSymbol: '\\vc{r}',

	//default letters for objects
	//volumes (3D)
	defaultLetterVolume: 'E',

	//line parameterization
	defaultLetterLineParameterization: '\\vc{r}',
	defaultLetterLineParameterizationComponent: 'r',

	//surface parameterization
	defaultLetterSurfaceParameterization: '\\vc{r}',
	defaultLetterSurfaceParameterizationComponent: 'r',
	
    }
  }

});

MathJax.Ajax.loadComplete("http://content.math.umn.edu/dev/static/mathinsight/mathjax/config/local/stewart.js");
