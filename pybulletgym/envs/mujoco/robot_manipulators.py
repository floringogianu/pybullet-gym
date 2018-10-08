from .robot_bases import MJCFBasedRobot
import numpy as np


class Reacher(MJCFBasedRobot):
	TARG_LIMIT = 0.27

	def __init__(self):
		MJCFBasedRobot.__init__(self, 'reacher.xml', 'body0', action_dim=2, obs_dim=9)

	def robot_specific_reset(self, bullet_client):
		self.jdict["target_x"].reset_current_position(
			self.np_random.uniform(low=-self.TARG_LIMIT, high=self.TARG_LIMIT), 0)
		self.jdict["target_y"].reset_current_position(
			self.np_random.uniform(low=-self.TARG_LIMIT, high=self.TARG_LIMIT), 0)
		self.fingertip = self.parts["fingertip"]
		self.target = self.parts["target"]
		self.central_joint = self.jdict["joint0"]
		self.elbow_joint = self.jdict["joint1"]
		self.central_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.elbow_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)

	def apply_action(self, a):
		assert (np.isfinite(a).all())
		self.central_joint.set_motor_torque(0.05 * float(np.clip(a[0], -1, +1)))
		self.elbow_joint.set_motor_torque(0.05 * float(np.clip(a[1], -1, +1)))

	def calc_state(self):
		target_x, target_vx = self.jdict["target_x"].current_position()
		target_y, target_vy = self.jdict["target_y"].current_position()

		qpos = np.array([j.current_position() for j in self.ordered_joints])  # shape (4,)
		qvel = np.array([j.current_relative_position()[1] for j in self.ordered_joints])  # shape (4,) # TODO: Add target pos and vel

		theta = qpos[:2]
		self.to_target_vec = np.array(self.fingertip.pose().xyz()) - np.array(self.target.pose().xyz())  # shape (3,)

		return np.concatenate([
			np.cos(theta),  # np.cos(theta),
			np.sin(theta),  # np.sin(theta),
			qpos.flat[2:],  # self.sim.data.qpos.flat[2:],
			qvel.flat[:2],  # self.sim.data.qvel.flat[:2],
			self.to_target_vec   # self.get_body_com("fingertip") - self.get_body_com("target")
		])

	def calc_potential(self):
		return -100 * np.linalg.norm(self.to_target_vec)


class Pusher(MJCFBasedRobot):
	min_target_placement_radius = 0.5
	max_target_placement_radius = 0.8
	min_object_to_target_distance = 0.1
	max_object_to_target_distance = 0.4

	def __init__(self):
		MJCFBasedRobot.__init__(self, 'pusher.xml', 'body0', action_dim=7, obs_dim=55)

	def robot_specific_reset(self, bullet_client):
		# parts
		self.fingertip = self.parts["tips_arm"]
		self.target = self.parts["goal"]
		self.object = self.parts["object"]

		# joints
		self.shoulder_pan_joint = self.jdict["r_shoulder_pan_joint"]
		self.shoulder_lift_joint = self.jdict["r_shoulder_lift_joint"]
		self.upper_arm_roll_joint = self.jdict["r_upper_arm_roll_joint"]
		self.elbow_flex_joint = self.jdict["r_elbow_flex_joint"]
		self.forearm_roll_joint = self.jdict["r_forearm_roll_joint"]
		self.wrist_flex_joint = self.jdict["r_wrist_flex_joint"]
		self.wrist_roll_joint = self.jdict["r_wrist_roll_joint"]

		self.target_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1)
		])

		# make length of vector between min and max_target_placement_radius
		self.target_pos = self.target_pos \
						  / np.linalg.norm(self.target_pos) \
						  * self.np_random.uniform(low=self.min_target_placement_radius,
												   high=self.max_target_placement_radius, size=1)

		self.object_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1)
		])

		# make length of vector between min and max_object_to_target_distance
		self.object_pos = self.object_pos \
						  / np.linalg.norm(self.object_pos - self.target_pos) \
						  * self.np_random.uniform(low=self.min_object_to_target_distance,
												   high=self.max_object_to_target_distance, size=1)

		# set position of objects
		self.zero_offset = np.array([0.45, 0.55])
		self.jdict["goal_slidex"].reset_current_position(self.target_pos[0] - self.zero_offset[0], 0)
		self.jdict["goal_slidey"].reset_current_position(self.target_pos[1] - self.zero_offset[1], 0)
		self.jdict["obj_slidex"].reset_current_position(self.object_pos[0] - self.zero_offset[0], 0)
		self.jdict["obj_slidey"].reset_current_position(self.object_pos[1] - self.zero_offset[1], 0)

		# randomize all joints TODO: Will this work or do we have to constrain this resetting in some way?
		self.shoulder_pan_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.shoulder_lift_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.elbow_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)

	def apply_action(self, a):
		assert (np.isfinite(a).all())
		self.shoulder_pan_joint.set_motor_torque(0.05 * float(np.clip(a[0], -1, +1)))
		self.shoulder_lift_joint.set_motor_torque(0.05 * float(np.clip(a[1], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[2], -1, +1)))
		self.elbow_flex_joint.set_motor_torque(0.05 * float(np.clip(a[3], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[4], -1, +1)))
		self.wrist_flex_joint.set_motor_torque(0.05 * float(np.clip(a[5], -1, +1)))
		self.wrist_roll_joint.set_motor_torque(0.05 * float(np.clip(a[6], -1, +1)))

	def calc_state(self):
		qpos = np.array([j.current_position() for j in self.ordered_joints])  # shape (11,)
		qvel = np.array([j.current_relative_position() for j in self.ordered_joints])  # shape (11,)
		tips_arm_body_com = self.fingertip.pose().xyz()  # shape (3,)
		object_body_com = self.object.pose().xyz()  # shape (3,)
		goal_body_com = self.target.pose().xyz()  # shape (3,)

		return np.concatenate([
			qpos.flat[:7],  # self.sim.data.qpos.flat[:7],
			qvel.flat[:7],  # self.sim.data.qvel.flat[:7],
			tips_arm_body_com,  # self.get_body_com("tips_arm"),
			object_body_com,  # self.get_body_com("object"),
			goal_body_com  # self.get_body_com("goal"),
		])


class Striker(MJCFBasedRobot):
	min_target_placement_radius = 0.1
	max_target_placement_radius = 0.8
	min_object_placement_radius = 0.1
	max_object_placement_radius = 0.8

	def __init__(self):
		MJCFBasedRobot.__init__(self, 'striker.xml', 'body0', action_dim=7, obs_dim=56)

	def robot_specific_reset(self, bullet_client):
		# parts
		self.fingertip = self.parts["tips_arm"]
		self.target = self.parts["coaster"] # TODO: goal does not show up, but coaster is great too
		self.object = self.parts["object"]

		# joints
		self.shoulder_pan_joint = self.jdict["r_shoulder_pan_joint"]
		self.shoulder_lift_joint = self.jdict["r_shoulder_lift_joint"]
		self.upper_arm_roll_joint = self.jdict["r_upper_arm_roll_joint"]
		self.elbow_flex_joint = self.jdict["r_elbow_flex_joint"]
		self.forearm_roll_joint = self.jdict["r_forearm_roll_joint"]
		self.wrist_flex_joint = self.jdict["r_wrist_flex_joint"]
		self.wrist_roll_joint = self.jdict["r_wrist_roll_joint"]

		self._min_strike_dist = np.inf
		self._striked = False
		self._strike_pos = None

		# reset position and speed of manipulator
		# TODO: Will this work or do we have to constrain this resetting in some way?
		self.shoulder_pan_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.shoulder_lift_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.elbow_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)

		self.zero_offset = np.array([0.45, 0.55, 0])
		self.object_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1)
		])

		# make length of vector between min and max_object_placement_radius
		self.object_pos = self.object_pos \
						  / np.linalg.norm(self.object_pos) \
						  * self.np_random.uniform(low=self.min_object_placement_radius,
												   high=self.max_object_placement_radius, size=1)

		# reset object position
		self.jdict["obj_slidex"].reset_current_position(self.object_pos[0] - self.zero_offset[0], 0)
		self.jdict["obj_slidey"].reset_current_position(self.object_pos[1] - self.zero_offset[1], 0)

		self.target_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1),#self.np_random.uniform(low=-1, high=1, size=1),
			np.array([-0.2])
		])

		# make length of vector between min and max_target_placement_radius
		# self.target_pos = self.target_pos \
		# 				  / np.linalg.norm(self.target_pos) \
		# 				  * self.np_random.uniform(low=self.min_target_placement_radius,
		# 										   high=self.max_target_placement_radius, size=1)

		self.jdict["goal_slidex"].reset_current_position(self.target_pos[0] - self.zero_offset[0], 0)
		self.jdict["goal_slidey"].reset_current_position(self.target_pos[1] - self.zero_offset[1], 0)
		#self.target.reset_pose(self.target_pos - self.zero_offset, np.array([0, 0, 0, 1]))

	def apply_action(self, a):
		assert (np.isfinite(a).all())
		self.shoulder_pan_joint.set_motor_torque(0.05 * float(np.clip(a[0], -1, +1)))
		self.shoulder_lift_joint.set_motor_torque(0.05 * float(np.clip(a[1], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[2], -1, +1)))
		self.elbow_flex_joint.set_motor_torque(0.05 * float(np.clip(a[3], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[4], -1, +1)))
		self.wrist_flex_joint.set_motor_torque(0.05 * float(np.clip(a[5], -1, +1)))
		self.wrist_roll_joint.set_motor_torque(0.05 * float(np.clip(a[6], -1, +1)))

	def calc_state(self):
		qpos = np.array([j.current_position() for j in self.ordered_joints]).flatten()  # shape (16,)
		qvel = np.array([j.current_relative_position() for j in self.ordered_joints]).flatten() # shape (15,)
		tips_arm_body_com = self.fingertip.pose().xyz()  # shape (3,)
		object_body_com = self.object.pose().xyz()  # shape (3,)
		goal_body_com = self.target.pose().xyz()  # shape (3,)

		return np.concatenate([
			qpos.flat[:7],  # self.sim.data.qpos.flat[:7],
			qvel.flat[:7],  # self.sim.data.qvel.flat[:7],
			tips_arm_body_com,  # self.get_body_com("tips_arm"),
			object_body_com,    # self.get_body_com("object"),
			goal_body_com       # self.get_body_com("goal"),
		])


class Thrower(MJCFBasedRobot):
	min_target_placement_radius = 0.1
	max_target_placement_radius = 0.8
	min_object_placement_radius = 0.1
	max_object_placement_radius = 0.8

	def __init__(self):
		MJCFBasedRobot.__init__(self, 'thrower.xml', 'body0', action_dim=7, obs_dim=48)

	def robot_specific_reset(self, bullet_client):
		# parts
		self.fingertip = self.parts["r_wrist_roll_link"]
		self.target = self.parts["goal"]
		self.object = self.parts["ball"]

		# joints
		self.shoulder_pan_joint = self.jdict["r_shoulder_pan_joint"]
		self.shoulder_lift_joint = self.jdict["r_shoulder_lift_joint"]
		self.upper_arm_roll_joint = self.jdict["r_upper_arm_roll_joint"]
		self.elbow_flex_joint = self.jdict["r_elbow_flex_joint"]
		self.forearm_roll_joint = self.jdict["r_forearm_roll_joint"]
		self.wrist_flex_joint = self.jdict["r_wrist_flex_joint"]
		self.wrist_roll_joint = self.jdict["r_wrist_roll_joint"]

		self._object_hit_ground = False
		self._object_hit_location = None

		# reset position and speed of manipulator
		# TODO: Will this work or do we have to constrain this resetting in some way?
		self.shoulder_pan_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.shoulder_lift_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.elbow_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.upper_arm_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_flex_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)
		self.wrist_roll_joint.reset_current_position(self.np_random.uniform(low=-3.14, high=3.14), 0)

		self.zero_offset = np.array([0.45, 0.55, 0])
		self.object_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1)
		])

		# make length of vector between min and max_object_placement_radius
		self.object_pos = self.object_pos \
						  / np.linalg.norm(self.object_pos) \
						  * self.np_random.uniform(low=self.min_object_placement_radius,
												   high=self.max_object_placement_radius, size=1)

		# reset object position
		self.parts["ball"].reset_pose(self.object_pos - self.zero_offset, np.array([0, 0, 0, 1]))

		self.target_pos = np.concatenate([
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1),
			self.np_random.uniform(low=-1, high=1, size=1)
		])

		# make length of vector between min and max_target_placement_radius
		self.target_pos = self.target_pos \
						  / np.linalg.norm(self.target_pos) \
						  * self.np_random.uniform(low=self.min_target_placement_radius,
												   high=self.max_target_placement_radius, size=1)

		self.parts["goal"].reset_pose(self.target_pos - self.zero_offset, np.array([0, 0, 0, 1]))

	def apply_action(self, a):
		assert (np.isfinite(a).all())
		self.shoulder_pan_joint.set_motor_torque(0.05 * float(np.clip(a[0], -1, +1)))
		self.shoulder_lift_joint.set_motor_torque(0.05 * float(np.clip(a[1], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[2], -1, +1)))
		self.elbow_flex_joint.set_motor_torque(0.05 * float(np.clip(a[3], -1, +1)))
		self.upper_arm_roll_joint.set_motor_torque(0.05 * float(np.clip(a[4], -1, +1)))
		self.wrist_flex_joint.set_motor_torque(0.05 * float(np.clip(a[5], -1, +1)))
		self.wrist_roll_joint.set_motor_torque(0.05 * float(np.clip(a[6], -1, +1)))

	def calc_state(self):
		qpos = np.array([j.current_position() for j in self.ordered_joints]).flatten()  # shape (16,)
		qvel = np.array([j.current_relative_position() for j in self.ordered_joints]).flatten()  # shape (15,)
		wrist_roll_link_body_com = self.fingertip.pose().xyz()  # shape (3,)
		ball_body_com = self.object.pose().xyz()  # shape (3,)
		goal_body_com = self.target.pose().xyz()  # shape (3,)

		return np.concatenate([
			qpos.flat[:7],  # self.sim.data.qpos.flat[:7],
			qvel.flat[:7],  # self.sim.data.qvel.flat[:7],
			wrist_roll_link_body_com,  # self.get_body_com("r_wrist_roll_link"),
			ball_body_com,  # self.get_body_com("ball"),
			goal_body_com, # self.get_body_com("goal"),
		])
