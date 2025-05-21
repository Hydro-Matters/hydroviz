import matplotlib.pyplot as plt
import numpy as np
try:
    import plotly.express as px
    import plotly.graph_objects as go
except:
    px = None
    go = None


class DischargePlot:
    """Object to handle generations of discharge plots
    """
    
    def __init__(self, title=None, date_units=None, verbose=True):
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

        # Store date units
        self._date_units = date_units
        if self._date_units == "days_since_2000" or self._date_units == "datetime64":
            self._dates_on_xaxis = True
        else:
            self._dates_on_xaxis = False

        # Empty lists of priors and products
        self._priors = []
        self._products = []
        
        self.xlabel = None
        self.ylabel = None
            
    def set_dates_xaxis(self):
        self._dates_on_xaxis = True
            
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
        
        # Convert times
        if times is not None:
            if self._date_units == "days_since_2000":
                times=np.datetime64("2000-01-01") + np.timedelta64(times, "D")
            
        self._priors.append({"times" : times, 
                             "values" : values, 
                             "label" : label, 
                             "color" : color,
                             "linestyle" : linestyle})
            
    def add_product(self, label, values, times=None, color=None, linestyle=None, ci=None):
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

        # Convert times
        if times is not None:
            if isinstance(times, np.ma.core.MaskedArray):
                times = times.filled(np.nan)
            if self._date_units == "days_since_2000":
                dt = np.array([np.timedelta64(days, "D") for days in times])
                times = np.datetime64("2000-01-01") + dt
        
        if ci is not None:
            lower = ci[:,0]
            higher = ci[:,1]
        else:
            lower = None
            higher = None
        
        self._products.append({"times" : times, 
                               "values" : values, 
                               "label" : label, 
                               "color" : color,
                               "linestyle" : linestyle,
                               "lower": lower,
                               "higher": higher})
            
    def add_axis_labels(self, xlabel, ylabel):
        self.xlabel = xlabel
        self.ylabel = ylabel
            
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
            if go is None:
                raise RuntimeError("plotly not found. Please install it or use backend='matplotlib'")
            if fig is None:
                fig = go.Figure()

        # Render products
        if self._date_units is not None:
            xmin = self._products[0]["times"][0]
            xmax = self._products[0]["times"][-1]
        else:
            xmin = np.inf
            xmax = -np.inf

        for product in self._products:
            if backend == "matplotlib":
                lab = product["label"]
                ax.plot(product["times"], product["values"], label=lab, c=product["color"], 
                        ls=product["linestyle"])
                if product["lower"] is not None and product["higher"] is not None:
                    ax.fill_between(product["times"], product["lower"], product["higher"], color=product["color"], alpha=0.2, label=f"{lab} - CI")
            elif backend == "plotly":
                # xmin = np.minimum(xmin, product["times"][0])
                # xmax = np.maximum(xmax, product["times"][-1])
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
                    # line = go.Line(x=[xmin, xmax], y=[prior["values"]]*2, name=prior["label"],
                    #            line={"color" : prior["color"], "width" : 2, "dash" : prior["linestyle"]})
                    # fig.add_trace(line)
                    fig.add_hline(y=prior["values"], name=prior["label"], line_color=prior["color"],
                                  line_width=4, line_dash=prior["linestyle"])
                else:
                    # line = go.Line(x=prior["times"], y=prior["values"], name=prior["label"],
                    #                line=dict(color=prior["color"], width=4, dash=prior["linestyle"]))
                    print("here...")
                    fig.add_hline(y=prior["values"], name=prior["label"], line_color=prior["color"],
                                  line_width=4, line_dash=prior["linestyle"])

        if backend == "matplotlib":
            if self._dates_on_xaxis:
                plt.xticks(rotation=45)
            if self._title is not None:
                plt.title(self._title)

            if self.xlabel is not None:
                plt.xlabel(self.xlabel)
            if self.ylabel is not None:
                plt.ylabel(self.ylabel)
            plt.legend()
            plt.tight_layout()
            plt.show()
        else:
            fig.update_layout(yaxis_tickformat='f',
                              xaxis_title='t',
                              yaxis_title='Discharge, cms')
            if self._title is not None:
                fig.suptitle(self._title)
            fig.show()
