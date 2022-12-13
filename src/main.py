import FunctionClass.Functions as fn
import Model.Model as m
import time
import os

PATH_DIR = os.getcwd()
print("="*50)
print("DIR: ",str(PATH_DIR))
print("="*50)
DEBUG = True

instance_segment  = {1: "200", 2: "400", 3: "800" , 4: "1000", 5: "1647"}
instance_microhub = {1: "10", 2: "30", 3: "46"}
instance_vehicle  = {1: "VAN_BIKE"}
horizont          = [6,12,18,24]

if __name__ == '__main__':
  for period in horizont:
    for keySegment, labelSegment in instance_segment.items():
      for keyMicrohub, labelMicrohub in instance_microhub.items():
        for keyVehicle, labelVehicle in instance_vehicle.items():
          print("="*30,"S"+labelSegment)
          print("="*30,"M"+labelMicrohub)
          print("="*30,"T"+str(period))
          # load datasets
          segments        = fn.load_segments(PATH_DIR, keySegment, DEBUG)
          microhubs       = fn.load_microhubs(PATH_DIR, keyMicrohub, DEBUG)
          vehicles        = fn.load_second_echelon_vehicles(PATH_DIR, DEBUG)
          matrix          = fn.load_distance_time_matrix(PATH_DIR, DEBUG)
          # computing ARCE
          arceCalculated  = fn.calculate_ARCE(segments, microhubs,  vehicles, matrix['distance'], period, DEBUG)
          # parameters for model
          params  = {
            'TimeLimit' : 1*30*60,
            'MIPGap'    : 0.01
          }
          # create object Model
          model = m.MP_2E(arceCalculated)
          # build the model
          model.build(period, segments, microhubs, vehicles)
          # setting parameters for solver
          model.setParams(params)
          
          # solver Model
          starTime = time.time()
          print(model.optimizeModel())
          durationExecute = time.time() - starTime
          print("="*10,"time %s" %(durationExecute))

          

      

