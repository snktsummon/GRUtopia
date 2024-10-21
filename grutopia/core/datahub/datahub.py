import datetime
from typing import Any, Dict, List

from grutopia.core.datahub.isaac_data import ActionData, IsaacData
from grutopia.core.datahub.model_data import ChainOfThoughtDataItem, ChatControlData, LogData, ModelData
from grutopia.core.util import AsyncRequest


class DataHub:
    """
    DataHub provides methods for interacting with Isaac Data.

    It contains:

    **Task**
       - Get task_name(): str
    **Robot**
       - Get action by task name
       - Set action by task name
       - Get obs by task name
       - Get obs by task name and robot name
       - Set obs by task name
    **Episode**
       - Get if episode finished
       - Set if episode finished
    **Webui chat**
       - Get chat log
       - Get chat control
       - Append chat log
       - Append chat control
       - Append cot

    """

    sim_remote = False
    chat_remote = True
    remote_address = ''
    WebBEUrl = ''
    GetAllObsUrl = ''
    SetObsUrl = ''
    GetObsByTaskNameUrl = ''
    SetActionsUrl = ''
    GetActionByTaskNameUrl = ''
    GenTaskIdUrl = ''
    SendChatControlUrl = ''
    SendCoTUrl = ''
    SendLogDataUrl = ''
    GetChatControlUrl = ''
    GetLogDataUrl = ''
    ClearUrl = ''

    @classmethod
    def datahub_init(
        cls,
        sim: str = 'local',
        chat: str = 'remote',
        remote: str = '127.0.0.1:9000',
    ):
        cls.sim_remote = sim == 'remote'
        cls.chat_remote = chat == 'remote'
        cls.remote_address = remote
        cls.set_attr()

    @classmethod
    def set_attr(cls) -> None:
        # BE url path init
        cls.WebBEUrl = f'http://{cls.remote_address}'  # noqa
        cls.GetAllObsUrl = cls.WebBEUrl + '/api/stream/get_all_obs'

        cls.SetObsUrl = cls.WebBEUrl + '/api/isaac/set_obs/'
        cls.GetObsByTaskNameUrl = cls.WebBEUrl + '/api/isaac/get_obs_by_id/'
        cls.GetObsByTaskNameAndRobotNameUrl = cls.WebBEUrl + '/api/isaac/get_obs_by_task_name_and_robot_name/'
        cls.SetActionsUrl = cls.WebBEUrl + '/api/isaac/set_actions/'
        cls.GetActionByTaskNameUrl = cls.WebBEUrl + '/api/isaac/get_action_by_id/'

        cls.GenTaskIdxUrl = cls.WebBEUrl + '/api/isaac/gen_task_idx'

        cls.SendChatControlUrl = cls.WebBEUrl + '/api/grutopia/append_chat_control_data'
        cls.SendCoTUrl = cls.WebBEUrl + '/api/grutopia/append_chain_of_thought_data'
        cls.SendLogDataUrl = cls.WebBEUrl + '/api/grutopia/append_log_data'
        cls.GetChatControlUrl = cls.WebBEUrl + '/api/grutopia/getChatList'
        cls.GetLogDataUrl = cls.WebBEUrl + '/api/grutopia/getloglist'

        cls.ClearUrl = cls.WebBEUrl + '/api/grutopia/clear'

    def __init__(self):
        pass

    @classmethod
    def get_actions_by_task_name(cls, task_name: str) -> Dict[str, Dict]:
        """
        Get action by task name.

        Args:
            task_name (str): task name

        Returns:
            Action of this
        """
        if cls.sim_remote:
            raise NotImplementedError('Remote get actions not implemented.')
        else:
            return IsaacData.get_action_by_task_name(task_name)

    @classmethod
    def get_obs_by_task_name(cls, task_name: str) -> Dict:
        """
        Get observation by task name

        Args:
            task_name (str): Task name

        Returns:
            obs (Any): Observation data
        """
        if cls.sim_remote:
            raise NotImplementedError('Remote get observation data not implemented.')
        else:
            return IsaacData.get_obs_by_task_name(task_name)

    @classmethod
    def get_obs_by_task_name_and_robot_name(cls, task_name: str, robot_name: str) -> Dict:
        """
        Get observation by task name

        Args:
            robot_name (str): robot name
            task_name (str): Task name

        Returns:
            obs (Any): Observation data
        """
        if cls.sim_remote:
            raise NotImplementedError('Remote get observation data not implemented.')
        else:
            return IsaacData.get_obs_by_task_name_and_robot_name(task_name, robot_name)

    @classmethod
    def set_obs_data(cls, obs: Dict[str, Dict[str, Any]]):
        """
        Set observation

        Args:
            obs (Dict[str, Dict[str, Any]]): Observation data with task_name as key.
        """
        if cls.sim_remote:
            raise NotImplementedError('Remote set observation data not implemented.')
        else:
            IsaacData.set_obs_data(obs)

    @classmethod
    def set_actions(cls, actions: Dict[str, ActionData]):
        """
        Set actions (dict, task_name(str) as key)

        Args:
            actions (Dict[str, ActionData]): Action data (dict) with task_name as key
        """
        if cls.sim_remote:
            raise NotImplementedError('Remote set actions not implemented.')
        else:
            IsaacData.set_actions(actions)

    @classmethod
    def get_episode_finished(cls, task_name: str) -> bool:
        """
        Get if episode finish by task name.

        Args:
            task_name (str): task name.

        Returns:
            bool: status of the task (finished or not)
        """
        if cls.sim_remote:
            raise NotImplementedError('get_episode_finish NotImplementedError')
        else:
            return IsaacData.get_episode_finished(task_name)

    @classmethod
    def set_episode_finished(cls, task_name: str):
        """
        Set episode finished by task_name.

        Args:
            task_name (str): task_name.
        """
        if cls.sim_remote:
            raise NotImplementedError('set_episode_finish NotImplementedError')
        else:
            IsaacData.set_episode_finished(task_name)

    @classmethod
    def gen_task_idx(cls) -> str:
        """
        Generate task index for new task.

        Returns:
            str: task index for the new task.
        """
        if cls.sim_remote:
            raise NotImplementedError('gen_task_idx NotImplementedError')
        else:
            return IsaacData.gen_task_idx()

    @classmethod
    def send_chain_of_thought(cls, cot: str, task_name: str) -> None:
        """
        chain of thought data

        Args:
            task_name (str): name of task, like id of chat group.
            cot (str): chain of thought data.
        """

        def cot_format(x):
            return {'type': 'text', 'value': x}

        res_data = [{'type': 'time', 'value': datetime.datetime.now().strftime('%H:%M')}]
        for i in cot:
            res_data.append(cot_format(i))
        if cls.chat_remote:
            raise NotImplementedError('Remote send chain of thought not implemented.')
        else:
            ModelData.append_chan_of_thought([ChainOfThoughtDataItem(**i) for i in res_data], task_name)

    @classmethod
    def send_chat_control(cls,
                          nickname: str,
                          text: str,
                          img: str = None,
                          role: str = 'user',
                          task_name: str = None,
                          at: list[str] = None,
                          parent_idx: int = -1) -> None:
        """Send a new message to the chatbox.

        Args:
            nickname (str): nickname displayed in the chatbox.
            text (str): text to send to the chatbox.
            img (str, optional): image to send to the chatbox. Defaults to None.
            role (str, optional): role name, user or agent. Defaults to "user".
            task_name (str): name of task, like id of chat group.
            at (list[str], optional): who this chat talk to. Defaults to All.
            parent_idx (int, optional): index of the parent message in chatbox. Defaults to -1.
        """
        res_data = {
            'type': role,
            'name': nickname,
            'time': datetime.datetime.now().strftime('%H:%M'),
            'message': text,
            'photo': None,  # TODO: Gen a photo with name(different color for each Agent or User)
            'img': img,
            'at': at,
            'parent_idx': parent_idx,
        }
        if cls.chat_remote:
            raise NotImplementedError('Remote send chat control not implemented.')
        else:
            ModelData.append_chat_control(ChatControlData(**res_data), task_name)

    @classmethod
    def send_log_data(
        cls,
        log_data: str,
        log_type: str = 'message',
        user: str = 'Bob',
        photo_url: str = None,
        task_name: str = None,
    ) -> None:
        """Send log data.

        Args:
            log_data (str): log data.
            log_type (str): type of log. 'message' or 'user'.
            user (str): logger name. default: Bob.
            photo_url (str): log photo url path.
            task_name (str): name of task, like id of chat group.
        """
        if log_type == 'message':
            res_data = {'type': 'message', 'message': log_data}
        else:  # user
            if log_type != 'user':
                return
            res_data = {
                'type': 'user',
                'name': user,
                'time': datetime.datetime.now().strftime('%H:%M'),
                'message': log_data,
                'photo': photo_url,
            }
        if cls.chat_remote:
            raise NotImplementedError('Remote send log data not implemented.')
        else:
            ModelData.append_log_data(LogData(**res_data), task_name)

    @classmethod
    def get_log_data(cls, task_name: str) -> List[Dict]:
        """
        Get log data.

        Args:
            task_name (str): name of task, like id of chat group.

        Returns:
            log_data (List[Dict]): log data.
        """
        if cls.chat_remote:
            raise NotImplementedError('Remote get log data not implemented.')
        return ModelData.get_log_data(task_name)

    @classmethod
    def get_chat_control(cls, task_name: str, read_idx: int) -> List[Dict[str, Any]]:
        """
        Get chat control data.

        Args:
            task_name (str): name of task, like id of chat group.
            read_idx (int): where to start reading chat control data(list).

        Returns:
            chat_control (List[Dict[str, Any]]): chat control data.
        """
        if cls.chat_remote:
            raise NotImplementedError('Remote get chat data not implemented.')
        else:
            return ModelData.get_chat_control(task_name, read_idx)

    @classmethod
    def clear(cls, uuid: str = 'none'):
        """
        Clear all data in webui.
        """
        if cls.chat_remote:
            AsyncRequest.post(uuid, cls.ClearUrl, None)
        else:
            ModelData.clear()
