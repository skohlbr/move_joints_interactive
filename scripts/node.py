#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 30/11/14

@author: Sam Pfeiffer

"""
# System imports
import random
import threading
import copy

# ROS imports
import rospy
from interactive_markers.interactive_marker_server import *
# messages
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from controller_manager_msgs.msg import ControllerState
# services
from controller_manager_msgs.srv import ListControllers, ListControllersRequest

# local imports
# Borrowed from Adolfo Rodriguez Tsouroukdissian
# at https://github.com/ros-controls/ros_controllers/blob/indigo-devel/rqt_joint_trajectory_controller/src/rqt_joint_trajectory_controller/joint_limits_urdf.py
# as the urdf_dom_py interface gives errors
from joint_limits_urdf import get_joint_limits
from im_for_link_class import LinkInteractiveMarker

CONTROLLER_MNGR_SRV = "/controller_manager/list_controllers"

class InteractiveJointTrajCtrl():
    def __init__(self):
        rospy.loginfo("Initializing InteractiveJointTrajCtrl")
        ctl_mngr_srv = rospy.ServiceProxy(CONTROLLER_MNGR_SRV, ListControllers)
        rospy.loginfo("Connecting to " + CONTROLLER_MNGR_SRV)
        ctl_mngr_srv.wait_for_service()
        rospy.loginfo("Connected.")
        
        self.rviz_config_str = ""
        
        req = ListControllersRequest()
        resp = ctl_mngr_srv.call(req)
        #ListControllersResponse()
        ctl_mngr_srv.close()
        joints_dict = get_joint_limits()
        publishers_dict = {}
        # dictionary that contains
        # key: head_controller
        # value:
        #   joints: ['head_1_joint', 'head_2_joint']
        #   publisher: pub
        #   ims: [interactive_marker_server_head_1_joint, interactive_marker_server_head_2_joint]
        for cs in resp.controller: # For every controller, create a publisher
            #cs = ControllerState()
            print "cs.name: " + str(cs.name),
            if len(cs.resources) > 0: # If the controller controls any joint only
                print "...controls joints!"
                publishers_dict[cs.name] = {}
                publishers_dict[cs.name]['joints'] = cs.resources
                cmd_topic = "/" + cs.name + "/command"
                publishers_dict[cs.name]['pub'] = rospy.Publisher(cmd_topic, JointTrajectory)
                publishers_dict[cs.name]['ims'] = []
                for joint_name in publishers_dict[cs.name]['joints']:
                    publishers_dict[cs.name]['ims'].append( LinkInteractiveMarker(joint_name, cs.name, cs.resources))
                    curr_im_rviz_cfg = self.create_im_config_rviz_block(joint_name)
                    self.rviz_config_str += curr_im_rviz_cfg
        
        self.save_rviz_config(self.rviz_config_str)
    
    def create_im_config_rviz_block(self, joint_name):
        ims_str = "ims_" + joint_name.replace('_joint', '')
        template = """        - Class: rviz/InteractiveMarkers
          Enable Transparency: true
          Enabled: true
          Name: """ + ims_str + """
          Show Axes: false
          Show Descriptions: false
          Show Visual Aids: false
          Update Topic: /""" + ims_str + """/update
          Value: true\n"""
        return template
    
    def save_rviz_config(self, rviz_cfg):
        import rospkg
        rp = rospkg.RosPack()
        path = rp.get_path("move_joints_interactive")
        rviztemplate = open(path + "/rviz/template_config.rviz", "r")
        full_file = rviztemplate.read()
        rviztemplate.close()
        #full_file =""
        final_file = full_file.replace("TEMPLATE_TO_FILL", rviz_cfg)
        output_f = open(path + "/rviz/current_rviz.rviz", "w")
        output_f.write(final_file)
        output_f.close()
        rospy.loginfo("\nRviz configuration file created at: " + path + "/rviz/current_rviz.rviz")
    
    
    def run(self):
        rospy.loginfo("Running!")
        while not rospy.is_shutdown():
            rospy.sleep(0.1)
        
if __name__ == '__main__':
    rospy.init_node('InteractiveJointTrajCtrl_')
    
    node = InteractiveJointTrajCtrl()
    node.run()
    
    