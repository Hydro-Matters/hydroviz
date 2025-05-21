try:
    from IPython import get_ipython
    ipy_shell =  get_ipython().__class__.__name__
    if ipy_shell != "ZMQInteractiveShell":
        print("This library is supposed to run on a Jupyter notebook. Please be aware that some method may not work")
    else:
        ipython = get_ipython()
        try:
            ipython.magic("matplotlib widget")
            print("Set interactive plots for matplotlib backend")
        except:
            print("Unable to set interactive plots for matplotlib backend")
except Exception as err:
    print("This library is supposed to run on a compatible Jupyter notebook. Please be aware that some method may not work")
    
        
