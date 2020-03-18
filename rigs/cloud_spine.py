import bpy
from bpy.props import *
from mathutils import *

from rigify.base_rig import stage

from ..definitions.driver import *
from ..definitions.custom_props import CustomProp
from .cloud_fk_chain import CloudChainRig

class CloudSpineRig(CloudChainRig):
	"""CloudRig spine"""

	def initialize(self):
		"""Gather and validate data about the rig."""
		super().initialize()
		
		self.display_scale *= 3

		self.ik_prop_name = "ik_spine"
		self.ik_stretch_name = "ik_stretch_spine"

	def get_segments(self, org_i, chain):
		"""Determine how many deform segments should be in a section of the chain."""
		segments = self.params.CR_deform_segments
		bbone_segments = self.params.CR_bbone_segments
		
		if (org_i == len(chain)-1):
			return (1, 1)
		
		return (segments, bbone_segments)

	@stage.prepare_bones
	def prepare_fk_spine(self):
		# Create Troso Master control
		self.mstr_torso = self.bone_infos.bone(
			name 					= "MSTR-Torso",
			source 					= self.org_chain[0],
			head 					= self.org_chain[0].center,
			# tail 					= self.org_chain[0].center + Vector((0, 0, self.scale)),
			custom_shape 			= self.load_widget("Torso_Master"),
			bone_group 				= 'Body: Main IK Controls',
		)

		# Create master (reverse) hip control
		self.mstr_hips = self.bone_infos.bone(
				name				= "MSTR-Hips",
				source				= self.org_chain[0],
				head				= self.org_chain[0].center,
				# tail 				= self.org_chain[0].center + Vector((0, 0, -self.scale)),
				custom_shape 		= self.load_widget("Hips"),
				custom_shape_scale 	= 0.7,
				parent				= self.mstr_torso,
				bone_group 			= "Body: Main IK Controls"
		)
		self.register_parent(self.mstr_torso, "Torso")
		self.mstr_torso.flatten()
		if self.params.CR_double_controls:
			double_mstr_pelvis = self.create_parent_bone(self.mstr_torso)
			double_mstr_pelvis.bone_group = 'Body: Main IK Controls Extra Parents'

		# Create FK bones
		# This should work with an arbitrary spine length. We assume that the chain ends in a neck and head.
		self.fk_chain = []
		fk_name = ""
		next_parent = self.mstr_torso
		for i, org_bone in enumerate(self.org_chain):
			fk_name = org_bone.name.replace("ORG", "FK")
			fk_bone = self.bone_infos.bone(
				name				= fk_name,
				source				= org_bone,
				custom_shape 		= self.load_widget("FK_Limb"),
				custom_shape_scale 	= 0.9 * org_bone.custom_shape_scale,
				parent				= next_parent,
				bone_group = "Body: Main FK Controls"
			)
			next_parent = fk_bone

			self.fk_chain.append(fk_bone)

			if i < len(self.org_chain)-2:	# Spine but not head and neck
				# Shift FK controls up to the center of their ORG bone
				org_bone = self.org_chain[i]
				fk_bone.put(org_bone.center)
				fk_bone.tail = self.org_chain[i+1].center
				#fk_bone.flatten()

				# Create a child corrective - Everything that would normally be parented to this FK bone should actually be parented to this child bone.
				fk_child_bone = self.bone_infos.bone(
					name = fk_bone.name.replace("FK", "FK-C"),
					source = fk_bone,
					custom_shape = fk_bone.custom_shape,
					custom_shape_scale = fk_bone.custom_shape_scale * 0.9,
					bone_group = 'Body: FK Helper Bones',
					parent = fk_bone
				)
				# Ideally, we would populate these bones' constraints from the metarig, because I think it will need tweaks for each character. But maybe I'm wrong.
				# TODO: Add FK-C constraints (4 Transformation Constraints).
				# I'm not sure if that should be done through the rig or customizable from the meta-rig. Maybe have defaults in here, but let the metarig overwrite?
				# But then we could just have defaults in the metarig as well...
				# But then reproportioning the rig becomes complicated, unless we store the constraint on the original bone, and somehow tell that constraint to go on the FK-C bone and target the FK bone...
				# It would be doable though... let's say a constraint is named FK-C:Transf_Fwd@FK - It would go on the FK-C-BoneName bone and its target would be FK-BoneName.
				# Could run into issues with armature constraint since it has multiple targets.
				next_parent = fk_child_bone
				fk_bone.fk_child = fk_child_bone
		
		# Head Hinge
		self.hinge_setup(
			bone = self.fk_chain[-1], 
			category = "Head",
			parent_bone = self.fk_chain[-2],
			hng_name = self.fk_chain[-1].name.replace("FK", "FK-HNG"),
			prop_bone = self.prop_bone,
			prop_name = "fk_hinge_head",
			limb_name = "Head",
			default_value = 1.0,
			head_tail = 1
		)

	@stage.prepare_bones
	def prepare_ik_spine(self):
		if not self.params.CR_create_ik_spine: return

		# Create master chest control
		self.mstr_chest = self.bone_infos.bone(
				name				= "MSTR-Chest", 
				source 				= self.org_chain[-4],
				head				= self.org_chain[-4].center,
				tail 				= self.org_chain[-4].center + Vector((0, 0, self.scale)),
				custom_shape 		= self.load_widget("Chest_Master"),
				custom_shape_scale 	= 0.7,
				parent				= self.mstr_torso,
				bone_group 			= "Body: Main IK Controls"
			)
		self.register_parent(self.mstr_chest, "Chest")

		if self.params.CR_double_controls:
			double_mstr_chest = self.create_parent_bone(self.mstr_chest)
			double_mstr_chest.bone_group = 'Body: Main IK Controls Extra Parents'
		
		self.mstr_hips.flatten()
		self.register_parent(self.mstr_hips, "Hips")

		self.ik_ctr_chain = []
		for i, fk_bone in enumerate(self.fk_chain[:-2]):
			ik_ctr_name = fk_bone.name.replace("FK", "IK-CTR")	# Equivalent of IK-CTR bones in Rain (Technically animator-facing, but rarely used)
			ik_ctr_bone = self.bone_infos.bone(
				name				= ik_ctr_name, 
				source				= fk_bone,
				custom_shape 		= self.load_widget("Oval"),
				bone_group 			= "Body: IK - Secondary IK Controls"
			)
			if i > len(self.fk_chain)-5:
				ik_ctr_bone.parent = self.mstr_chest
			else:
				ik_ctr_bone.parent = self.mstr_torso
			self.ik_ctr_chain.append(ik_ctr_bone)
		
		# Reverse IK (IK-R) chain - root parented to MSTR-Chest. Damped track to IK-CTR of one lower index.
		next_parent = self.mstr_chest
		self.ik_r_chain = []
		for i, fk_bone in enumerate(reversed(self.fk_chain[1:-2])):	# We skip the first spine, the neck and the head.
			ik_r_name = fk_bone.name.replace("FK", "IK-R")
			ik_r_bone = self.bone_infos.bone(
				name		= ik_r_name,
				source 		= fk_bone,
				tail 		= self.fk_chain[-i+1].head,
				parent		= next_parent,
				bone_group = 'Body: IK-MCH - IK Mechanism Bones',
				hide_select	= self.mch_disable_select
			)
			next_parent = ik_r_bone
			self.ik_r_chain.append(ik_r_bone)
			ik_r_bone.add_constraint(self.obj, 'DAMPED_TRACK',
				subtarget = self.ik_ctr_chain[-i+1].name
			)
		
		# IK chain
		next_parent = self.mstr_hips
		self.ik_chain = []
		for i, fk_bone in enumerate(self.fk_chain[:-2]):
			ik_name = fk_bone.name.replace("FK", "IK")
			ik_bone = self.bone_infos.bone(
				name = ik_name,
				source = fk_bone,
				head = copy.copy(self.fk_chain[i-1].head) if i>0 else copy.copy(self.def_bones[0].head),
				tail = fk_bone.head,
				parent = next_parent,
				bone_group = 'Body: IK-MCH - IK Mechanism Bones',
				hide_select	= self.mch_disable_select
			)
			self.ik_chain.append(ik_bone)
			next_parent = ik_bone
			
			if i > 0:
				influence_unit = 0.5   #1 / (len(self.fk_chain) - 3)	# Minus three because there are no IK bones for the head and neck, and no stretchy constraint on the first IK spine bone. TODO: Allow arbitrary spine length.
				influence = influence_unit * i
				# IK Stretch Copy Location
				con_name = "Copy Location (Stretchy Spine)"
				ik_bone.add_constraint(self.obj, 'COPY_LOCATION', true_defaults=True,
					name = con_name,
					target = self.obj,
					subtarget = self.ik_r_chain[i-2].name,
					head_tail = 1,
				)
				drv = Driver()
				drv.expression = "var * %f" %influence
				var = drv.make_var("var")
				var.type = 'SINGLE_PROP'
				var.targets[0].id_type='OBJECT'
				var.targets[0].id = self.obj
				var.targets[0].data_path = 'pose.bones["%s"]["%s"]' %(self.prop_bone.name, self.ik_stretch_name)

				data_path = f'constraints["{con_name}"].influence'
				ik_bone.drivers[data_path] = drv

				ik_bone.add_constraint(self.obj, 'COPY_ROTATION', true_defaults=True,
					target = self.obj,
					subtarget = self.ik_ctr_chain[i-1].name
				)
				self.ik_ctr_chain[i-1].custom_shape_transform = ik_bone
			
			damped_track_target = self.ik_r_chain[-i+1].name
			head_tail = 1
			if i == len(self.fk_chain)-3:
				# Special treatment for last IK bone...
				damped_track_target = self.ik_ctr_chain[-1].name
				head_tail = 0
				self.mstr_chest.custom_shape_transform = ik_bone
				if self.params.CR_double_controls:
					self.mstr_chest.parent.custom_shape_transform = ik_bone

			ik_bone.add_constraint(self.obj, 'DAMPED_TRACK',
				subtarget = damped_track_target,
				head_tail = head_tail
			)

		# Attach FK to IK
		for i, ik_bone in enumerate(self.ik_chain[1:]):
			fk_bone = self.fk_chain[i]
			con_name = "Copy Transforms IK"
			fk_bone.add_constraint(self.obj, 'COPY_TRANSFORMS', true_defaults=True,
				name = con_name,
				target = self.obj,
				subtarget = ik_bone.name
			)
			drv = Driver()
			drv.expression = "var"
			var = drv.make_var("var")
			var.type = 'SINGLE_PROP'
			var.targets[0].id_type='OBJECT'
			var.targets[0].id = self.obj
			var.targets[0].data_path = 'pose.bones["%s"]["%s"]' %(self.prop_bone.name, self.ik_prop_name)

			data_path = f'constraints["{con_name}"].influence'
			fk_bone.drivers[data_path] = drv
		
		# Store info for UI
		info = {
			"prop_bone"		: self.prop_bone.name,
			"prop_id" 		: self.ik_stretch_name,
		}
		self.store_ui_data("ik_stretches", "spine", "Spine", info)

		info = {
			"prop_bone"		: self.prop_bone.name,
			"prop_id"		: self.ik_prop_name,
		}
		self.store_ui_data("ik_switches", "spine", "Spine", info)

		# Create custom properties
		self.prop_bone.custom_props[self.ik_prop_name] = CustomProp(self.ik_prop_name, default=0.0)
		self.prop_bone.custom_props[self.ik_stretch_name] = CustomProp(self.ik_stretch_name, default=1.0)

	@stage.prepare_bones
	def prepare_def_str_spine(self):
		# Tweak some display things
		for i, str_bone in enumerate(self.str_bones):
			str_bone.use_custom_shape_bone_size = False
			str_bone.custom_shape_scale = 0.15
		
		for i, def_bone in enumerate(self.def_bones):
			if i == len(self.def_bones)-2:
				# Neck DEF bone
				def_bone.bbone_easeout = 0	# TODO: this doesn't work?
		
		# The last DEF bone should copy the scale of the FK bone. (Or maybe each of them should? And maybe all FK chains, not just the spine? TODO)
		last_def = self.def_bones[-1]
		# last_def.add_constraint(self.obj, 'COPY_SCALE', prepend=True, true_defaults=True, target=self.obj, subtarget=self.fk_chain[-1].name)
		# Nevermind, just inherit scale for now, it works nice when the neck STR scales the head in this case.
		last_def.inherit_scale = 'FULL'

	@stage.prepare_bones
	def prepare_org_spine(self):
		#	FK Follows IK with Copy Transforms (same as Rain)
		#	(We can drive shape keys with FK rotation)

		# Parent ORG to FK
		for i, org_bone in enumerate(self.org_chain):
			if i == 0:
				org_bone.parent = self.mstr_hips
			elif i > len(self.org_chain)-2:
				# Last two STR bones should both be parented to last FK bone(the head)
				org_bone.parent = self.fk_chain[-1]
			elif hasattr(self.fk_chain[i-1], 'fk_child'):
				org_bone.parent = self.fk_chain[i-1].fk_child
			else:
				print("This shouldn't happen?")
				org_bone.parent = self.fk_chain[i-1]
		
		# Change any ORG- children of the final spine bone to be owned by the neck bone instead. This is needed because the responsibility of all ORG- bones is shifted down by one, because of the "FK-controls-in-the-center" setup.
		for b in self.bone_infos.bones:
			if b.parent==self.org_chain[-3] and b.name.startswith("ORG-"):
				b.parent = self.org_chain[-2]

	##############################
	# Parameters

	@classmethod
	def add_parameters(cls, params):
		""" Add the parameters of this rig type to the
			RigifyParameters PropertyGroup
		"""
		super().add_parameters(params)

		params.CR_spine_length = IntProperty(
			name="Spine Length",
			description="Number of bones on the chain until the spine ends and the neck begins. The spine and neck can both be made up of an arbitrary number of bones. The final bone of the chain is always treated as the head.",
			default=3,
			min=3,
			max=99
		)
		params.CR_create_ik_spine = BoolProperty(
			name="Create IK Setup",
			description="If disabled, this spine rig will only have FK controls",
			default=True
		)
		params.CR_double_controls = BoolProperty(
			name="Double Controls", 
			description="Make duplicates of the main spine controls",
			default=True,
		)

	@classmethod
	def parameters_ui(cls, layout, params):
		"""Create the ui for the rig parameters."""
		super().parameters_ui(layout, params)

		layout.label(text="Spine Settings")
		layout = layout.box()

		layout.prop(params, "CR_spine_length")
		layout.prop(params, "CR_create_ik_spine")
		layout.prop(params, "CR_double_controls")

class Rig(CloudSpineRig):
	pass


def create_sample(obj):
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('Spine')
    bone.head = 0.0000, 0.0018, 0.8211
    bone.tail = 0.0000, -0.0442, 1.0134
    bone.roll = 0.0000
    bone.use_connect = False
    bone.bbone_x = 0.0135
    bone.bbone_z = 0.0135
    bone.head_radius = 0.0114
    bone.tail_radius = 0.0122
    bone.envelope_distance = 0.1306
    bone.envelope_weight = 1.0000
    bone.use_envelope_multiply = 0.0000
    bones['Spine'] = bone.name
    bone = arm.edit_bones.new('RibCage')
    bone.head = 0.0000, -0.0442, 1.0134
    bone.tail = 0.0000, -0.0458, 1.1582
    bone.roll = 0.0000
    bone.use_connect = True
    bone.bbone_x = 0.0124
    bone.bbone_z = 0.0124
    bone.head_radius = 0.0122
    bone.tail_radius = 0.0121
    bone.envelope_distance = 0.1231
    bone.envelope_weight = 1.0000
    bone.use_envelope_multiply = 0.0000
    bone.parent = arm.edit_bones[bones['Spine']]
    bones['RibCage'] = bone.name
    bone = arm.edit_bones.new('Chest')
    bone.head = 0.0000, -0.0458, 1.1582
    bone.tail = 0.0000, -0.0148, 1.2805
    bone.roll = 0.0000
    bone.use_connect = True
    bone.bbone_x = 0.0108
    bone.bbone_z = 0.0108
    bone.head_radius = 0.0121
    bone.tail_radius = 0.0118
    bone.envelope_distance = 0.1000
    bone.envelope_weight = 1.0000
    bone.use_envelope_multiply = 0.0000
    bone.parent = arm.edit_bones[bones['RibCage']]
    bones['Chest'] = bone.name
    bone = arm.edit_bones.new('Neck')
    bone.head = 0.0000, -0.0148, 1.2805
    bone.tail = 0.0000, -0.0277, 1.3921
    bone.roll = 0.0000
    bone.use_connect = True
    bone.bbone_x = 0.0056
    bone.bbone_z = 0.0056
    bone.head_radius = 0.0118
    bone.tail_radius = 0.0138
    bone.envelope_distance = 0.0739
    bone.envelope_weight = 1.0000
    bone.use_envelope_multiply = 0.0000
    bone.parent = arm.edit_bones[bones['Chest']]
    bones['Neck'] = bone.name
    bone = arm.edit_bones.new('Head')
    bone.head = 0.0000, -0.0277, 1.3921
    bone.tail = 0.0000, -0.0528, 1.6157
    bone.roll = 0.0000
    bone.use_connect = True
    bone.bbone_x = 0.0113
    bone.bbone_z = 0.0113
    bone.head_radius = 0.0138
    bone.tail_radius = 0.0583
    bone.envelope_distance = 0.0799
    bone.envelope_weight = 1.0000
    bone.use_envelope_multiply = 0.0000
    bone.parent = arm.edit_bones[bones['Neck']]
    bones['Head'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['Spine']]
    pbone.rigify_type = 'cloud_spine'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'XYZ'
    try:
        pbone.rigify_parameters.CR_double_root = False
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.CR_double_controls = False
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.CR_sharp_sections = False
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.CR_deform_segments = 1
    except AttributeError:
        pass
    try:
        pbone.rigify_parameters.CR_bbone_segments = 6
    except AttributeError:
        pass
    pbone = obj.pose.bones[bones['RibCage']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['Chest']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['Neck']]
    pbone.rigify_type = ''
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'
    pbone = obj.pose.bones[bones['Head']]
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