import gym
import bikey.bicycle
import os


def run_environment(message_queue, response_queue, name_queue):
    """
    Sets up an environment and controls it.

    The code in this function should always run in its own process, so
    CPU-bound code does not block the server. Queues are used to communicate
    with the server. When None is received through the message_queue, this
    process will shut down.

    Arguments:
    message_queue -- Any requests will come in through this queue
    response_queue -- Once a request is done, a confirmation needs to be put in
        this queue.
    name_queue -- A queue that provides working directories to supported
        environments. Currently only used for BicycleEnv-v0.
    """
    # print("Initialized new process")
    initialized = False
    reset = False

    env = None

    while True:
        # process incoming messages
        message = message_queue.get()

        if message is None:
            # handler thread wants this process to die
            if initialized:
                env.close()

            # note: the associated thread is not waiting for a response, so we
            # can just exit this process
            break  # let this process die

        command = message['command']

        if command == 'init':
            if initialized:
                # TODO already initialized, command inappropriate
                continue

            data = message['data']

            if data['env'] == 'BicycleEnv-v0':
                # TODO make this env ID check future proof for new versions
                name = name_queue.get()
                if 'config' in data:
                    data['config']['working_dir'] = name
                else:
                    data['config'] = {'working_dir': name}

                # only a name has been generated, now create the directory
                os.makedirs(name)

            env = gym.make(data['env'], **data['config'])
            initialized = True
            # print("Initialized environment")

            response_queue.put({
                'command': 'confirm',
                'data': {
                    # send the client information about the observation and action
                    # spaces so it can reconstruct them
                    'observation_space': gym_space_to_dict(env.observation_space),
                    'action_space': gym_space_to_dict(env.action_space)
                }
            })

        elif command == 'reset':
            if not initialized:
                # TODO not yet initialized, command inappropriate
                continue

            observation = env.reset()
            reset = True

            # print('Reset the environment')

            response_queue.put({
                'command': 'confirm',
                'data': {
                    'observation': observation
                }
            })

        elif command == 'step':
            if not reset:
                # TODO not yet reset, command inappropriate
                continue

            action = message['data']['action']
            observation, reward, done, info = env.step(action)

            response_queue.put({
                'command': 'confirm',
                'data': {
                    'observation': observation,
                    'reward': reward,
                    'done': done,
                    'info': info
                }
            })

        elif command == 'shut_down_server':
            # a client has requested the entire server to shut down

            if initialized:
                env.close()

            # this event needs to be communicated with the rest of the server
            response_queue.put(None)
            break  # now let this process die

        else:
            # TODO unsupported command, raise error
            # do not forget to put an item on the response queue, or the thread
            # will block, and so will everything else
            pass


def gym_space_to_dict(space):
    """
    Writes the properties of an observation or action space to a dictionary.

    This can be sent across a network using JSON, to allow the space to be
    reconstructed on a different machine. For now this method only supports
    gym.spaces.Box and gym.spaces.Discrete.

    Arguments:
    space -- The observation or action space to be described.

    Returns:
    A dictionary containing properties of a gym space, i.e. the type of space,
    upper and lower bounds, shape, and data type.
    """
    if type(space) is gym.spaces.Box:
        return {
            'space': 'gym.spaces.Box',
            'low': space.low.tolist(),
            'high': space.high.tolist(),
            'shape': space.shape,
            'dtype': str(space.dtype)
        }
    elif type(space) is gym.spaces.Discrete:
        return {
            'space': 'gym.spaces.Discrete',
            'n': space.n
        }
    else:
        # not supported
        raise TypeError("Cannot convert anything but the gym.spaces.Box space\
                        to JSON")
