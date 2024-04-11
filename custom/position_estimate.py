from bluepy.btle import Scanner, DefaultDelegate
from datetime import datetime
import numpy as np
import math

BT_ADDR_1 = '58:c3:56:07:95:ea'  # Beacon of this address will be the origin (0,0)
BT_ADDR_2 = '58:c3:56:07:ac:a9'  # Beacon of this address will be (10, 0)
BT_ADDR_3 = '58:c3:56:07:b6:45'  # Beacon of this address will be (0, 10)
DIST_MAP = {BT_ADDR_1 : 0, BT_ADDR_2 : 0, BT_ADDR_3 : 0} #hashmap with dummy values, minutely faster than array

#Coordinates of the 3 beacons respectively
P1 = (0.0,0.0) #for BT1 in this code
P2 = (3.0,0.0) #for BT2 in this code
P3 = (0.0,2.0) #for BT3 in this code
RSSI_1M = -61

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

class PositionEstimator(object):
        
    def get_coordinates(self):
        #rssi_list = self.get_distances_2() #This line right here is your error lmao
        DIST_MAP = self.get_distances_2()
        r1 = DIST_MAP[BT_ADDR_1]
        r2 = DIST_MAP[BT_ADDR_2]
        r3 = DIST_MAP[BT_ADDR_3]
        
        #What is this for??
        p1 = np.array(P1)
        p2 = np.array(P2)
        p3 = np.array(P3) 
        
        # To understand the math, read {https://math.stackexchange.com/questions/884807/find-x-location-using-3-known-x-y-location-using-trilateration}
    
        A = -2*P1[0] + 2*P2[0]
        B = -2*P1[1] + 2*P2[1]
        C = r1**2-r2**2-P1[0]**2+P2[0]**2-P1[1]**2+P2[1]**2

        
        D = -2*P2[0] + 2*P3[0]
        E = -2*P2[1] + 2*P3[1]
        F = r2**2-r3**2-P2[0]**2+P3[0]**2-P2[1]**2+P3[1]**2
        
        #print("ABCDEF ", A," , ", B," , ", C," , ", D," , ", E," , ", F)
        unknown_matrix = np.array([[A,B],[D,E]])
        constant_matrix = np.array([C,F])
        
        #get least squares solution because distance measured may result in singular matrix
        dynamic_point, _, _, _ = np.linalg.lstsq(unknown_matrix, constant_matrix, rcond=None) 
        #print("Dynamic point " , dynamic_point)
        return dynamic_point
        
    
    def get_distances(self):
        scanner = Scanner().withDelegate(ScanDelegate())
        bt1_count = 1
        bt2_count = 1
        bt3_count = 1
        DIST_MAP = {BT_ADDR_1 : 0, BT_ADDR_2 : 0, BT_ADDR_3 : 0}
        time_start = datetime.now()
        time_now = datetime.now()
        elapsed_time = (time_now - time_start).total_seconds()
        while elapsed_time < 3:
            devices = scanner.scan(0.1) 
            for dev in devices:
                if dev.addr in DIST_MAP:
                # Calculate approximate distance
                    rssi = dev.rssi
                    distance = 10 ** ((RSSI_1M - rssi) / 20.0)
                    DIST_MAP[dev.addr] += distance
                    if dev.addr == BT_ADDR_1:
                        bt1_count += 1
                    if dev.addr == BT_ADDR_2:
                        bt2_count += 1
                    if dev.addr == BT_ADDR_3:
                        bt3_count += 1
            time_now = datetime.now()
            elapsed_time = (time_now - time_start).total_seconds()
        #average it out
        DIST_MAP[BT_ADDR_1] = DIST_MAP[BT_ADDR_1]/bt1_count
        DIST_MAP[BT_ADDR_2] = DIST_MAP[BT_ADDR_2]/bt2_count
        DIST_MAP[BT_ADDR_3] = DIST_MAP[BT_ADDR_3]/bt3_count
        #print(DIST_MAP[BT_ADDR_3])
        return DIST_MAP
        
        
        #Average RSSI, not distances..
    def get_distances_2(self):   
        scanner = Scanner().withDelegate(ScanDelegate())
        bt1_count = 0
        bt2_count = 0
        bt3_count = 0
        DIST_MAP = {BT_ADDR_1 : 0, BT_ADDR_2 : 0, BT_ADDR_3 : 0}
        RSSI_MAP = {BT_ADDR_1 : 0, BT_ADDR_2 : 0, BT_ADDR_3 : 0}
        time_start = datetime.now()
        time_now = datetime.now()
        elapsed_time = (time_now - time_start).total_seconds()
        while (elapsed_time < 0.75 or bt1_count<1 or bt2_count<1 or bt3_count<1) :
            devices = scanner.scan(0.1) 
            for dev in devices:
                if dev.addr in DIST_MAP:
                # Calculate average rssi
                    rssi = dev.rssi
                    RSSI_MAP[dev.addr] += rssi
                    if dev.addr == BT_ADDR_1:
                        bt1_count += 1
                    if dev.addr == BT_ADDR_2:
                        bt2_count += 1
                    if dev.addr == BT_ADDR_3:
                        bt3_count += 1
            time_now = datetime.now()
            elapsed_time = (time_now - time_start).total_seconds()
            
            #escape loop clause
            if (elapsed_time>15):
                bt1_count += 1
                bt2_count += 1
                bt3_count += 1
                print("Bluetooth reading missing")
                break
            
            
        #average it out
        RSSI_MAP[BT_ADDR_1] = RSSI_MAP[BT_ADDR_1]/bt1_count
        RSSI_MAP[BT_ADDR_2] = RSSI_MAP[BT_ADDR_2]/bt2_count
        RSSI_MAP[BT_ADDR_3] = RSSI_MAP[BT_ADDR_3]/bt3_count
        
        DIST_MAP[BT_ADDR_1] = 10 ** ((RSSI_1M - RSSI_MAP[BT_ADDR_1]) / 20.0)
        DIST_MAP[BT_ADDR_2] = 10 ** ((RSSI_1M - RSSI_MAP[BT_ADDR_2]) / 20.0)
        DIST_MAP[BT_ADDR_3] = 10 ** ((RSSI_1M - RSSI_MAP[BT_ADDR_3]) / 20.0)      
        
        return DIST_MAP
         
    def trilaterate(self):
        """
        Trilateration algorithm to find the coordinates of a point in a 2D plane
        based on the distances to three known points.

        Args:
            distances (list): List of three distances from the unknown point to each of the known points.
            points (list): List of three known points, each represented as a tuple (x, y).
            
        Returns:
            tuple: Coordinates of the unknown point (x, y).
        """
        
        
        # Extract coordinates of known points
        x1, y1 = points[0]
        x2, y2 = points[1]
        x3, y3 = points[2]

        # Extract distances to known points
        self.get_distances_2()
        d1, d2, d3 = DIST_MAP[BT_ADDR_1], DIST_MAP[BT_ADDR_2] , DIST_MAP[BT_ADDR_3] 
        
        # Trilateration equations
        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2 * (x3 - x2)
        E = 2 * (y3 - y2)
        F = d2**2 - d3**2 - x2**2 + x3**2 - y2**2 + y3**2

        # Solve linear system of equations
        x = (C * E - F * B) / (E * A - B * D)
        y = (C * D - A * F) / (B * D - A * E)
        #print("Calculated x, y" , x, " , " , y)
        return x, y

if __name__ == '__main__':
    print(PositionEstimator().get_coordinates())
