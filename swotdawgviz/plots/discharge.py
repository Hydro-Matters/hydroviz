import matplotlib.pyplot as plt
import numpy as np
try:
    import plotly.express as px
    import plotly.graph_objects as go
except:
    px = None
    go = None


class DischargePlot:
    
    def __init__(self, title=None, verbose=True):
        """Create a discharge plot
        
        Parameters
        ----------
        title : str
            Title of the plot
        verbose : bool
            True to enable verbose output
        """

        # Store title
        self._title = title

        # Empty lists of priors and products
        self._priors = []
        self._products = []
            
    def add_prior(self, label, values, times=None, color=None, linestyle=None):
        """Add prior data
        
        Parameters
        ----------
        label : str
            Label for the legend
        values : float or iterable
            Constant or timeseries prior discharge
        times : float or iterable (or None)
            Times corresponding to the discharge values
        color : str (or other choices, see Matplotlib)
            Color of the corresponding line (see Matplotlib)
        linestyle : str
            Style of the corresponding line (see Matplotlib)
        """
            
        self._priors.append({"times" : times, 
                             "values" : values, 
                             "label" : label, 
                             "color" : color,
                             "linestyle" : linestyle})
            
    def add_product(self, label, values, times=None, color=None, linestyle=None):
        """Add product (algorithm output) data
        
        Parameters
        ----------
        label : str
            Label for the legend
        values : float or iterable
            Constant or timeseries product discharge
        times : float or iterable (or None)
            Times corresponding to the discharge values
        color : str (or other choices, see Matplotlib)
            Color of the corresponding line (see Matplotlib)
        linestyle : str
            Style of the corresponding line (see Matplotlib)
        """
        
        self._products.append({"times" : times, 
                               "values" : values, 
                               "label" : label, 
                               "color" : color,
                               "linestyle" : linestyle})
            

    def render(self, fig=None, ax=None, backend="matplotlib"):
        """Render the plot
        
        Parameters
        ----------
        fig : matplotlib.Figure
            Figure to add plot to
        ax : matplotlib.Axis
            Axis to add plot to
        """
        
        if backend == "matplotlib":
            if fig is None:
                fig = plt.figure()
            if ax is None:
                ax = plt.gca()
        elif backend == "plotly":
            if fig is None:
                fig = go.Figure()

        # Render products
        xmin = np.PINF
        xmax = np.NINF
        for product in self._products:
            if backend == "matplotlib":
                ax.plot(product["times"], product["values"], label=product["label"], c=product["color"], 
                        ls=product["linestyle"])
            elif backend == "plotly":
                xmin = np.minimum(xmin, product["times"][0])
                xmax = np.maximum(xmax, product["times"][-1])
                line = go.Line(x=product["times"], y=product["values"], name=product["label"],
                               line={"color" : product["color"], "width" : 2, "dash" : product["linestyle"]})
                fig.add_trace(line)
                
        # Render priors
        for prior in self._priors:
            if backend == "matplotlib":
                if prior["times"] is None:
                    ax.axhline(prior["values"], label=prior["label"], c=prior["color"], ls=prior["linestyle"])
                else:
                    ax.plot(prior["times"], prior["values"], label=prior["label"], c=prior["color"], 
                            ls=prior["linestyle"])
            elif backend == "plotly":
                if prior["times"] is None:
                    line = go.Line(x=[xmin, xmax], y=[prior["values"]]*2, name=prior["label"],
                               line={"color" : prior["color"], "width" : 2, "dash" : prior["linestyle"]})
                    fig.add_trace(line)
                else:
                    line = go.Line(x=prior["times"], y=prior["values"], name=prior["label"],
                                   line=dict(color=prior["color"], width=4, dash=prior["linestyle"]))
                    fig.add_trace(line)
        
        if backend == "matplotlib":
            plt.legend()
            plt.show()
        else:
            fig.update_layout(yaxis_tickformat='f',
                              xaxis_title='Days since 01 jan. 2000',
                              yaxis_title='Discharge, cms')
            fig.show()
