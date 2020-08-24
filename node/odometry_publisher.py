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

vx = 0.1
vy = -0.1
vth = 0.1

current_time = 0
last_time = 0
imu_data = Imu()


def callback(data):
    rospy.loginfo(rospy.get_caller_id())

    global current_time
    global last_time
    global imu_data

    global x
    global y
    global th

    global vx
    global vy
    global vth

    current_time = rospy.Time.now()
    imu_data = data

    vx = imu_data.linear_acceleration.x / 100
    vy = imu_data.linear_acceleration.y / 100
    vth = imu_data.angular_velocity.z

    # compute odometry in a typical way given the velocities of the robot
    dt = (current_time - last_time).to_sec()
    delta_x = (vx * cos(th) - vy * sin(th)) * dt
    delta_y = (vx * sin(th) + vy * cos(th)) * dt
    delta_th = vth * dt

    x += delta_x
    y += delta_y
    th += delta_th

    # since all odometry is 6DOF we'll need a quaternion created from yaw
    _, __, th = euler_from_quaternion(imu_data.orientation.x,
                                        imu_data.orientation.y,
                                        imu_data.orientation.z,
                                        imu_data.orientation.w)
    odom_quat = tf.transformations.quaternion_from_euler(0, 0, th)
    # odom_quat = (imu_data.orientation.x,
    #             imu_data.orientation.y, 
    #             imu_data.orientation.z, 
    #             imu_data.orientation.w)

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
    rospy.spin()
