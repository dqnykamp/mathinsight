import os    
import tempfile
os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from django import http
from numpy import *


def linegraph(f, xmin=0, xmax=100, xlabel=None, ylabel=None, linestyle='', ylim=None, linewidth=None):
    

    fig=Figure(facecolor='w', edgecolor='w')
    ax=fig.add_subplot(111)
    x=linspace(xmin,xmax,200)
    y=[]
    try:
        y=f(x)
        if not linestyle:
            linestyle='-k'
        if not linewidth:
            linewidth=1
        ax.plot(x, y, linestyle, linewidth=linewidth)
    except TypeError:  # check if f is a list of functions
        try:
            for (i, fsub) in enumerate(f):
                y=fsub(x)
                if not linestyle:
                    ls='-k'
                elif type(linestyle) is unicode:
                    ls=linestyle
                else:
                    try:
                        if linestyle[i]:
                            ls=linestyle[i]
                        else:
                            ls='-k'
                    except IndexError:
                        ls='-k'
                if not linewidth:
                    lw=1
                elif type(linewidth) is float or type(linewidth) is int:
                    lw=linewidth
                else:
                    try:
                        if linewidth[i]:
                            lw=linewidth[i]
                        else:
                            lw=1
                    except IndexError:
                        lw=1
                ax.plot(x,y, ls, linewidth=lw)

        except:
            raise
    
    if ylim:
        if ylim[0] is None:
            if ylim[1] is not None: 
                ax.set_ylim(ymax=ylim[1])
        else:
            if ylim[1] is None:
                ax.set_ylim(ymin=ylim[0])
            else:
                ax.set_ylim(ylim)

    ax.set_xlim([xmin,xmax])


        
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    canvas=FigureCanvas(fig)
    response=http.HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response
