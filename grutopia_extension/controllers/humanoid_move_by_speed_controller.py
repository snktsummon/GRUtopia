from typing import List

import numpy as np
import torch
from omni.isaac.core.articulations import ArticulationSubset
from omni.isaac.core.scenes import Scene
from omni.isaac.core.utils.types import ArticulationAction
from rsl_rl.modules.actor_critic import ActorCritic

import grutopia.core.util.gym as gymutil
import grutopia.core.util.math as math_utils
from grutopia.core.robot.controller import BaseController
from grutopia.core.robot.robot import BaseRobot
from grutopia.core.util.rsl_rl import pickle
from grutopia_extension.config.controllers import HumanoidMoveBySpeedControllerModel


class RLPolicy:
    """RL policy for h1 locomotion."""

    def __init__(self, path: str) -> None:
        self.policy_cfg = {
            'class_name': 'ActorCritic',
            'init_noise_std': 1.0,
            'actor_hidden_dims': [1024, 512, 256],
            'critic_hidden_dims': [1024, 512, 256],
            'activation': 'elu',
        }
        self.empirical_normalization = False

        num_obs = 471
        num_critic_obs = 471
        self.env_actions = 19
        self.actor_critic = ActorCritic(num_obs, num_critic_obs, self.env_actions, **self.policy_cfg)
        self.load(path=path)

    def load(self, path: str, load_optimizer=False):
        loaded_dict = torch.load(path, pickle_module=pickle)
        self.actor_critic.load_state_dict(loaded_dict['model_state_dict'])
        if self.empirical_normalization:
            self.obs_normalizer.load_state_dict(loaded_dict['obs_norm_state_dict'])
            self.critic_obs_normalizer.load_state_dict(loaded_dict['critic_obs_norm_state_dict'])
        if load_optimizer:
            self.alg.optimizer.load_state_dict(loaded_dict['optimizer_state_dict'])
        self.current_learning_iteration = loaded_dict['iter']
        return loaded_dict['infos']

    def get_inference_policy(self, device=None):
        self.eval_mode()  # switch to evaluation mode (dropout for example)
        if device is not None:
            self.actor_critic.to(device)
        policy = self.actor_critic.act_inference
        return policy

    def eval_mode(self):
        self.actor_critic.eval()
        if self.empirical_normalization:
            self.obs_normalizer.eval()
            self.critic_obs_normalizer.eval()


@BaseController.register('HumanoidMoveBySpeedController')
class HumanoidMoveBySpeedController(BaseController):
    """Controller class converting locomotion speed control action to joint positions for H1 robot."""

    """
    joint_names_sim and joint_names_gym define default joint orders in isaac-sim and isaac-gym.
    """
    joint_names_sim = [
        'left_hip_yaw_joint',
        'right_hip_yaw_joint',
        'torso_joint',
        'left_hip_roll_joint',
        'right_hip_roll_joint',
        'left_shoulder_pitch_joint',
        'right_shoulder_pitch_joint',
        'left_hip_pitch_joint',
        'right_hip_pitch_joint',
        'left_shoulder_roll_joint',
        'right_shoulder_roll_joint',
        'left_knee_joint',
        'right_knee_joint',
        'left_shoulder_yaw_joint',
        'right_shoulder_yaw_joint',
        'left_ankle_joint',
        'right_ankle_joint',
        'left_elbow_joint',
        'right_elbow_joint',
    ]

    joint_names_gym = [
        'left_hip_yaw_joint',
        'left_hip_roll_joint',
        'left_hip_pitch_joint',
        'left_knee_joint',
        'left_ankle_joint',
        'right_hip_yaw_joint',
        'right_hip_roll_joint',
        'right_hip_pitch_joint',
        'right_knee_joint',
        'right_ankle_joint',
        'torso_joint',
        'left_shoulder_pitch_joint',
        'left_shoulder_roll_joint',
        'left_shoulder_yaw_joint',
        'left_elbow_joint',
        'right_shoulder_pitch_joint',
        'right_shoulder_roll_joint',
        'right_shoulder_yaw_joint',
        'right_elbow_joint',
    ]

    def __init__(self, config: HumanoidMoveBySpeedControllerModel, robot: BaseRobot, scene: Scene) -> None:
        super().__init__(config=config, robot=robot, scene=scene)
        self.applied_joint_positions = None
        self._policy = RLPolicy(path=config.policy_weights_path).get_inference_policy(device='cpu')
        self.joint_subset = None
        self.joint_names = config.joint_names
        self.gym_adapter = gymutil.gym_adapter(self.joint_names_gym, self.joint_names_sim)
        if self.joint_names is not None:
            self.joint_subset = ArticulationSubset(self.robot.isaac_robot, self.joint_names)
        self._old_joint_positions = np.zeros(19)
        self.policy_input_obs_num = 471
        self._old_policy_obs = np.zeros(self.policy_input_obs_num)
        self._apply_times_left = (
            0  # Specifies how many times the action generated by the policy needs to be repeatedly applied.
        )

    def forward(
        self,
        forward_speed: float = 0,
        rotation_speed: float = 0,
        lateral_speed: float = 0,
    ) -> ArticulationAction:
        if self._apply_times_left > 0:
            self._apply_times_left -= 1
            if self.joint_subset is None:
                return ArticulationAction(joint_positions=self.applied_joint_positions)
            return self.joint_subset.make_articulation_action(
                joint_positions=self.applied_joint_positions, joint_velocities=None
            )

        # Get obs for policy.
        robot_base = self.robot.get_robot_base()
        base_pose_w = robot_base.get_world_pose()
        base_quat_w = torch.tensor(base_pose_w[1]).reshape(1, -1)
        base_lin_vel_w = torch.tensor(robot_base.get_linear_velocity()).reshape(1, -1)
        base_ang_vel_w = torch.tensor(robot_base.get_angular_velocity()[:]).reshape(1, -1)
        base_lin_vel = np.array(math_utils.quat_rotate_inverse(base_quat_w, base_lin_vel_w).reshape(-1))
        base_ang_vel = np.array(math_utils.quat_rotate_inverse(base_quat_w, base_ang_vel_w).reshape(-1))

        projected_gravity = torch.tensor([[0.0, 0.0, -1.0]], device='cpu', dtype=torch.float)
        projected_gravity = np.array(math_utils.quat_rotate_inverse(base_quat_w, projected_gravity).reshape(-1))
        joint_pos = (
            self.joint_subset.get_joint_positions()
            if self.joint_subset is not None
            else self.robot.isaac_robot.get_joint_positions()
        )
        joint_vel = (
            self.joint_subset.get_joint_velocities()
            if self.joint_subset is not None
            else self.robot.isaac_robot.get_joint_velocities()
        )
        default_dof_pos = np.array(
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.4, -0.4, 0.0, 0.0, 0.8, 0.8, 0.0, 0.0, -0.4, -0.4, 0.0, 0.0]
        )

        joint_pos -= default_dof_pos

        base_height = base_pose_w[0][2]
        ankle_height = self.robot.get_ankle_height()
        relative_base_height = base_height - ankle_height
        heights = np.clip(relative_base_height - 0.5 - np.zeros(121), -1.0, 1.0) * 5.0

        # Set action command.
        tracking_command = np.array([forward_speed, lateral_speed, rotation_speed, 0.0], dtype=np.float32)

        raw_policy_obs = np.concatenate(
            [
                tracking_command * np.array([2.0, 2.0, 0.25, 1.0]),
                base_ang_vel * 0.25,
                projected_gravity,
                self.gym_adapter.sim2gym(joint_pos),
                self.gym_adapter.sim2gym(joint_vel) * 0.05,
                self.gym_adapter.sim2gym(self._old_joint_positions.reshape(19)),
                base_lin_vel * 2.0,
                heights,
            ]
        )
        policy_obs = np.concatenate([self._old_policy_obs[70:350], raw_policy_obs])
        self._old_policy_obs = policy_obs
        policy_obs = policy_obs.reshape(1, 471)

        # Infer with policy.
        with torch.inference_mode():
            joint_positions: np.ndarray = (
                self._policy(torch.tensor(policy_obs, dtype=torch.float32).to('cpu')).detach().numpy() * 0.25
            )
            joint_positions = joint_positions[0]
            joint_positions = self.gym_adapter.gym2sim(joint_positions)
            self._old_joint_positions = joint_positions * 4
            self.applied_joint_positions = joint_positions + default_dof_pos
            self._apply_times_left = 3

        if self.joint_subset is None:
            return ArticulationAction(joint_positions=self.applied_joint_positions)
        return self.joint_subset.make_articulation_action(
            joint_positions=self.applied_joint_positions, joint_velocities=None
        )

    def action_to_control(self, action: List | np.ndarray) -> ArticulationAction:
        """Convert input action (in 1d array format) to joint positions to apply.

        Args:
            action (List | np.ndarray): 3-element 1d array containing:
              0. forward_speed (float)
              1. lateral_speed (float)
              2. rotation_speed (float)

        Returns:
            ArticulationAction: joint positions to apply.
        """
        assert len(action) == 3, 'action must contain 3 elements'

        return self.forward(forward_speed=action[0], lateral_speed=action[1], rotation_speed=action[2])
