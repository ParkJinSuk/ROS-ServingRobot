#!/usr/bin/env python

# https://gist.github.com/atotto/f2754f75bedb6ea56e3e0264ec405dcf
# modified ros_odometry_publisher_example.py

import math
from math import sin, cos, pi

import rospy
import tf
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Pose, Quaternion, Twist, Vector3
from sensor_msgs.msg import Imu

# variable
x = 0.0
y = 0.0
th = 0.0

vx = 0
vy = 0
vth = 0

ROBOT_WHEEL_DIAMETER = 0.095

current_time = 0
last_time = 0
imu_data = Imu()
imu_angle = Twist()

def callback(data):

    global current_time
    global last_time
    global imu_data

    global x
    global y
    global th

    global vx
    global vy
    global vth

    global ax_calibration
    global ay_calibration

    imu_data = data

    current_time = rospy.Time.now()
    dt = (current_time - last_time).to_sec()
    # rospy.loginfo("dt : {}".format(dt)) # 0.01sec

    vth = imu_data.angular_velocity.z
    th_rad = th * 3.141592 / 180
    # rospy.loginfo("th_rad : {}\t".format(th_rad))

    # rospy.loginfo("x: {}\ty: {}".format(imu_data.linear_acceleration.x,imu_data.linear_acceleration.y))
    # rospy.loginfo("vx : {}\tvy : {}\tvth : {}".format(vx, vy, vth))

    # compute odometry in a typical way given the velocities of the robot
    delta_x = (vx * cos(th_rad) - vy * sin(th_rad)) * dt
    delta_y = (vx * sin(th_rad) + vy * cos(th_rad)) * dt
    
    x += delta_x
    y += delta_y
    rospy.loginfo("x : {}\ty : {}".format(x, y))


    # since all odometry is 6DOF we'll need a quaternion created from yaw
    # _, __, th_dec = euler_from_quaternion(imu_data.orientation.x,
    #                                     imu_data.orientation.y,
    #                                     imu_data.orientation.z,
    #                                     imu_data.orientation.w)

    # insert euler(radian)
    odom_quat = tf.transformations.quaternion_from_euler(0, 0, th_rad)
    
    # first, we'll publish the transform over tf
    odom_broadcaster.sendTransform(
        (x, y, 0.),
        odom_quat,
        current_time,
        "base_footprint",
        "odom"
    )

    # next, we'll publish the odometry message over ROS
    odom = Odometry()
    odom.header.stamp = current_time
    odom.header.frame_id = "odom"

    # set the position
    odom.pose.pose = Pose(Point(x, y, 0.), Quaternion(*odom_quat))

    # set the velocity
    odom.child_frame_id = "base_footprint"
    odom.twist.twist = Twist(Vector3(vx, vy, 0), Vector3(0, 0, vth))

    # publish the message
    odom_pub.publish(odom)

    last_time = current_time

def callback_angle(data):
    global th
    th = data.angular.z

def callback_enc(data):
    global vx
    global vy

    encoder_data = data # dec/sec

    linear_velocity_x = encoder_data.angular.x * (ROBOT_WHEEL_DIAMETER * 3.1415 / 360)
    linear_velocity_y = encoder_data.angular.y * (ROBOT_WHEEL_DIAMETER * 3.1415 / 360)

    vx = linear_velocity_x
    vy = linear_velocity_y

def euler_from_quaternion(x, y, z, w):
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    X = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    Z = math.degrees(math.atan2(t3, t4))

    return X, Y, Z


if __name__ == "__main__":
    rospy.init_node('odometry_publisher')

    odom_pub = rospy.Publisher("odom", Odometry, queue_size=50)
    odom_broadcaster = tf.TransformBroadcaster()

    current_time = rospy.Time.now()
    last_time = rospy.Time.now()
    
    rospy.Subscriber('imu', Imu, callback, queue_size=50)
    rospy.Subscriber('imu_angle', Twist, callback_angle, queue_size=50)
    rospy.Subscriber('encoder_vel', Twist, callback_enc, queue_size=50)
    rospy.spin()
