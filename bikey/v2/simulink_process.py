import bikey.utils
import matlab.engine


def matlab_handler(config, server_port, events):
    # Start Matlab
    engine = matlab.engine.start_matlab(config['matlab_params'])
    engine.cd(config['working_dir'], nargout = 0)

    # Copy the required simulation files
    bikey.utils.set_template_dir(config['template_dir'])
    if config["copy_simulink"]:
        # copy the requested simulink model
        bikey.utils.copy_from_template_dir(config["simulink_file"],
                                           config["working_dir"])
    if config["copy_spacar"]:
        # copy the requested spacar model
        bikey.utils.copy_from_template_dir(config["spacar_file"],
                                           config["working_dir"])

    model = config['simulink_file'][:-4]  # strip the file extension

    # engine.open_system(model, nargout = 0) # use GUI
    handle = engine.load_system(model)
    print("Matlab loaded")

    engine.set_param(f'{model}/server port', 'value', str(server_port), nargout=0)
    print("Provided simulink model with port number")

    output = engine.sim(model)

    # TODO create a loop that allows multiple simulations to be run in this process

    # TODO close simulink model and quit matlab

    print("End of process")
