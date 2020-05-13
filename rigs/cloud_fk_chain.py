import bpy
from bpy.props import BoolProperty
from mathutils import Vector

from rigify.base_rig import stage

from ..definitions.driver import Driver
from .cloud_chain import CloudChainRig

class CloudFKChainRig(CloudChainRig):
	"""CloudRig FK chain."""

	description = "FK chain with squash and stretch controls."

	def initialize(self):
		"""Gather and validate data about the rig."""
		super().initialize()

	def prepare_fk_chain(self):
		self.fk_chain = []
		fk_name = ""

		for i, org_bone in enumerate(self.org_chain):
			fk_name = org_bone.name.replace("ORG", "FK")
			fk_bone = self.bone_infos.bone(
				name				= fk_name
				,source				= org_bone
				,custom_shape 		= self.load_widget("FK_Limb")
				,custom_shape_scale = org_bone.custom_shape_scale
				,parent				= self.bones.parent
				,bone_group			= self.bone_groups["FK Controls"]
				,layers				= self.bone_layers["FK Controls"]
			)
			if i > 0:
				# Parent FK bone to previous FK bone.
				fk_bone.parent = self.fk_chain[-1]
			if self.params.CR_center_all_fk:
				self.create_dsp_bone(fk_bone, center=True)
			if self.params.CR_counter_rotate_str:
				str_bone = self.main_str_bones[i]
				str_bone.add_constraint(self.obj, 'TRANSFORM'
					,subtarget				= fk_bone.name
					,map_from				= 'ROTATION'
					,map_to					= 'ROTATION'
					,use_motion_extrapolate = True
					,from_max_x_rot			= 1
					,from_max_y_rot			= 1
					,from_max_z_rot			= 1
					,to_max_x_rot			= -0.5
					,to_max_y_rot			= -0.5
					,to_max_z_rot			= -0.5
				)
			self.fk_chain.append(fk_bone)

	def prepare_org_chain(self):
		# Find existing ORG bones
		# Add Copy Transforms constraints targetting FK.
		for i, org_bone in enumerate(self.org_chain):
			fk_bone = self.bone_infos.find(org_bone.name.replace("ORG", "FK"))

			org_bone.add_constraint(self.obj, 'COPY_TRANSFORMS', true_defaults=True, target=self.obj, subtarget=fk_bone.name, name="Copy Transforms FK")

	def prepare_bones(self):
		super().prepare_bones()
		self.prepare_fk_chain()
		self.prepare_org_chain()

	##############################
	# Parameters

	@classmethod
	def add_bone_sets(cls, params):
		""" Create parameters for this rig's bone sets. """
		super().add_bone_sets(params)
		cls.add_bone_set(params, "FK Controls", preset=1, default_layers=[cls.default_layers('FK_MAIN')])

	@classmethod
	def add_parameters(cls, params):
		""" Add the parameters of this rig type to the
			RigifyParameters PropertyGroup
		"""

		params.CR_show_fk_settings = BoolProperty(name="FK Rig")
		params.CR_counter_rotate_str = BoolProperty(
			 name		 = "Counter-Rotate STR"
			,description = "Main STR- bones will counter half the rotation of their parent FK bones. This forces Deform Segments parameter to be 1. Will result in easier to pose smooth curves"
			,default	 = False
		)
		params.CR_center_all_fk = BoolProperty(
			 name		 = "Display FK in center"
			,description = "Display all FK controls' shapes in the center of the bone, rather than the beginning of the bone"
			,default	 = False
		)

		super().add_parameters(params)


	@classmethod
	def parameters_ui(cls, layout, params):
		""" Create the ui for the rig parameters.
		"""
		ui_rows = super().parameters_ui(layout, params)

		icon = 'TRIA_DOWN' if params.CR_show_fk_settings else 'TRIA_RIGHT'
		layout.prop(params, "CR_show_fk_settings", toggle=True, icon=icon)
		if not params.CR_show_fk_settings: return ui_rows

		layout.prop(params, "CR_counter_rotate_str")
		layout.prop(params, "CR_center_all_fk")

		return ui_rows

class Rig(CloudFKChainRig):
	pass

def create_sample(obj):
	# generated by rigify.utils.write_metarig
	bpy.ops.object.mode_set(mode='EDIT')
	arm = obj.data

	bones = {}

	bone = arm.edit_bones.new('FK_Chain_1')
	bone.head = 0.0000, 0.0000, 0.0000
	bone.tail = 0.0000, -0.5649, 0.0000
	bone.roll = -3.1416
	bone.use_connect = False
	bone.bbone_x = 0.0399
	bone.bbone_z = 0.0399
	bone.head_radius = 0.0565
	bone.tail_radius = 0.0282
	bone.envelope_distance = 0.1412
	bone.envelope_weight = 1.0000
	bone.use_envelope_multiply = 0.0000
	bones['FK_Chain_1'] = bone.name
	bone = arm.edit_bones.new('FK_Chain_2')
	bone.head = 0.0000, -0.5649, 0.0000
	bone.tail = 0.0000, -1.1299, 0.0000
	bone.roll = -3.1416
	bone.use_connect = True
	bone.bbone_x = 0.0399
	bone.bbone_z = 0.0399
	bone.head_radius = 0.0282
	bone.tail_radius = 0.0565
	bone.envelope_distance = 0.1412
	bone.envelope_weight = 1.0000
	bone.use_envelope_multiply = 0.0000
	bone.parent = arm.edit_bones[bones['FK_Chain_1']]
	bones['FK_Chain_2'] = bone.name
	bone = arm.edit_bones.new('FK_Chain_3')
	bone.head = 0.0000, -1.1299, 0.0000
	bone.tail = 0.0000, -1.6948, -0.0000
	bone.roll = -3.1416
	bone.use_connect = True
	bone.bbone_x = 0.0399
	bone.bbone_z = 0.0399
	bone.head_radius = 0.0565
	bone.tail_radius = 0.0565
	bone.envelope_distance = 0.1412
	bone.envelope_weight = 1.0000
	bone.use_envelope_multiply = 0.0000
	bone.parent = arm.edit_bones[bones['FK_Chain_2']]
	bones['FK_Chain_3'] = bone.name
	bone = arm.edit_bones.new('FK_Chain_4')
	bone.head = 0.0000, -1.6948, -0.0000
	bone.tail = 0.0000, -2.2598, 0.0000
	bone.roll = -3.1416
	bone.use_connect = True
	bone.bbone_x = 0.0399
	bone.bbone_z = 0.0399
	bone.head_radius = 0.0565
	bone.tail_radius = 0.0565
	bone.envelope_distance = 0.1412
	bone.envelope_weight = 1.0000
	bone.use_envelope_multiply = 0.0000
	bone.parent = arm.edit_bones[bones['FK_Chain_3']]
	bones['FK_Chain_4'] = bone.name

	bpy.ops.object.mode_set(mode='OBJECT')
	pbone = obj.pose.bones[bones['FK_Chain_1']]
	pbone.rigify_type = 'cloud_fk_chain'
	pbone.lock_location = (False, False, False)
	pbone.lock_rotation = (False, False, False)
	pbone.lock_rotation_w = False
	pbone.lock_scale = (False, False, False)
	pbone.rotation_mode = 'QUATERNION'
	try:
		pbone.rigify_parameters.CR_subdivide_deform = 10
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_controls_for_handles = True
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_show_spline_ik_settings = True
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_show_display_settings = False
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_curve_handle_ratio = 2.5
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_rotatable_handles = False
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_hook_name = "Cable"
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_show_chain_settings = True
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_sharp_sections = True
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_bbone_segments = 6
	except AttributeError:
		pass
	try:
		pbone.rigify_parameters.CR_show_fk_settings = True
	except AttributeError:
		pass
	pbone = obj.pose.bones[bones['FK_Chain_2']]
	pbone.rigify_type = ''
	pbone.lock_location = (False, False, False)
	pbone.lock_rotation = (False, False, False)
	pbone.lock_rotation_w = False
	pbone.lock_scale = (False, False, False)
	pbone.rotation_mode = 'QUATERNION'
	pbone = obj.pose.bones[bones['FK_Chain_3']]
	pbone.rigify_type = ''
	pbone.lock_location = (False, False, False)
	pbone.lock_rotation = (False, False, False)
	pbone.lock_rotation_w = False
	pbone.lock_scale = (False, False, False)
	pbone.rotation_mode = 'QUATERNION'
	pbone = obj.pose.bones[bones['FK_Chain_4']]
	pbone.rigify_type = ''
	pbone.lock_location = (False, False, False)
	pbone.lock_rotation = (False, False, False)
	pbone.lock_rotation_w = False
	pbone.lock_scale = (False, False, False)
	pbone.rotation_mode = 'QUATERNION'

	bpy.ops.object.mode_set(mode='EDIT')
	for bone in arm.edit_bones:
		bone.select = False
		bone.select_head = False
		bone.select_tail = False
	for b in bones:
		bone = arm.edit_bones[bones[b]]
		bone.select = True
		bone.select_head = True
		bone.select_tail = True
		arm.edit_bones.active = bone

	return bones