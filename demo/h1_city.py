from grutopia.core.env import Env
from grutopia.core.runtime import SimulatorRuntime
from grutopia.core.util.container import is_in_container
from grutopia_extension import import_extensions

headless = False
webrtc = False

if is_in_container():
    headless = True
    webrtc = True
file_path = './GRUtopia/demo/configs/h1_city.yaml'

sim_runtime = SimulatorRuntime(config_path=file_path, headless=headless, webrtc=webrtc)

import_extensions()
# import custom extensions here.

env = Env(sim_runtime)
obs, _ = env.vector_reset()
print(f'========INIT OBS{obs}=============')

i = 0
actions = {'h1_0': {'move_with_keyboard': []}}

while env.simulation_app.is_running():
    i += 1
    env_actions = {}
    for task_runtime in env.active_runtimes.values():
        env_actions[task_runtime.name] = actions

    env.step(actions=env_actions)

    if i % 100 == 0:
        print(i)

env.simulation_app.close()
