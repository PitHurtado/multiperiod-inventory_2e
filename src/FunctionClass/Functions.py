from FunctionClass.Classes import Segment, MicroHub, Vehicle
import json
import pandas as pd
import math

instanceSegments  = {1:"/dataIn/instance_segment_200.csv",
                    2:"/dataIn/instance_segment_400.csv",
                    3:"/dataIn/instance_segment_800.csv",
                    4:"/dataIn/instance_segment_1000.csv",
                    5:"/dataIn/instance_segment_1647.csv"}
instanceMicroHubs = {1:"/dataIn/instance_mh_10.csv",
                    2:"/dataIn/instance_mh_30.csv",
                    3:"/dataIn/instance_mh_46.csv"}
instanceMicroHubsCapacity = "/dataIn/Base MicroHub Capacity.xlsx"
instanceVehicles          = "/dataIn/Base Vehiculos.xlsx"
instanceDistanceMatrix    = "/dataIn/Base Matriz Distancia (Pesimista).csv"

def load_distance_time_matrix(path_distance_matrix: str, DEBUG = False) -> dict[str, dict]:
  df_distance           = pd.read_csv(path_distance_matrix+instanceDistanceMatrix)
  distance_mh_zc        = dict([((df_distance.OSM_ID[i],df_distance.GEOCODIGO[i]),df_distance.loc[i,"distance.value"]/1000 ) for i in range(len(df_distance))])
  time_mh_zc            = dict([((df_distance.OSM_ID[i],df_distance.GEOCODIGO[i]),df_distance.loc[i,"duration.value"]/3600 ) for i in range(len(df_distance))])
  timeTraffic_mh_zc     = dict([((df_distance.OSM_ID[i],df_distance.GEOCODIGO[i]),df_distance.loc[i,"duration_in_traffic.value"]/3600 ) for i in range(len(df_distance))])
  if DEBUG:
    print(distance_mh_zc)
  
  matrix = {
    "distance"    : distance_mh_zc,
    "time"        : time_mh_zc,
    "timeTraffic" : timeTraffic_mh_zc
  }
  return matrix

def load_segments(path_segment: str, num_instance: int, DEBUG = False) -> list[Segment]:
  segments  = []
  df_segments = pd.read_csv(path_segment + instanceSegments[num_instance])
  for lab, row in df_segments.iterrows():
    customersByPeriod = [row["customer_"+str(i)] for i in range(24)]
    demandByPeriod    = [row["demand_"+str(i)] for i in range(24)]
    new_segment   = Segment(int(row['GEOCODIGO']),
                            float(row['lon']),
                            float(row['lat']),
                            customersByPeriod,
                            demandByPeriod,
                            float(row['Vel_promedio']),
                            float(row['area_km2']))
    segments.append(new_segment)
  if DEBUG:
    print("-"*100)
    print("Count of SEGMENTS: ", len(segments))
    print("First Segment:")
    print(json.dumps(segments[0].__dict__,indent=2,default=str))
  return segments

def load_microhubs(path_microhub: str, num_instance: int, DEBUG = False) -> list[MicroHub]:  
  microHubs = []
  df_mh           = pd.read_csv(path_microhub+instanceMicroHubs[num_instance])
  df_mh_capacity  = pd.read_excel(path_microhub+instanceMicroHubsCapacity)
  for lab, row in df_mh.iterrows():
    costFixed         = [row['cf_'+str(i)]*1000 for i in range(24)]
    costOperation     = {}
    costInventory     = [row['ci_'+str(i)]*1000 for i in range(24)]
    capacityOperation = {}
    capacityInventory = df_mh_capacity[row['osm_id']][3]
    areaKm            = float(row['area_m2']/1000)
    timeFromDC        = float(row['duration_in_traffic.value']/3600)
    costFromDC        = int(timeFromDC*20000)
    for j in range(1,11): # de 10, 20, 30, 40, .. ,100 % de capacidad
      cap_name = "cap_"+str(j/10)
      costOperation[cap_name]     = [row['co_'+str(i)]*1000*j/10 for i in range(24)]
      capacityOperation[cap_name] = df_mh_capacity[row['osm_id']][2]*j/10
    new_microhub = MicroHub(int(row['osm_id']),
                            float(row['longitude']),
                            float(row['latitude']),
                            costFixed,
                            costOperation,
                            costInventory,
                            costFromDC,
                            capacityOperation,
                            capacityInventory,
                            timeFromDC,
                            areaKm)
    microHubs.append(new_microhub)
  if DEBUG:
    print("-"*100)
    print("Cantidad MICROHUB: ", len(microHubs))
    print("First MicroHub:")
    print(json.dumps(microHubs[0].__dict__,indent=1, default=str))
  return microHubs

def load_second_echelon_vehicles(path_vehicle: str, DEBUG = False) -> list[Vehicle]:
  vehicles    = []
  df_vehicle  = pd.read_excel(path_vehicle+instanceVehicles)
  for lab,row in df_vehicle.iterrows():
    new_vehicle   = Vehicle(row['id'],
                            row['capacity'],
                            row['costByDistance'],
                            row['costByTime'],
                            row['costFixed'],
                            row['speedLinehaul'],
                            row['timeSetupRoute'],
                            row['speedInterStop'], 
                            row['timeServiceMaximum'],
                            row['timeServicePerStop']
                            )
    vehicles.append(new_vehicle) 
  if DEBUG:
    print("-"*100)
    print("Cantidad VEHICLE: ", len(vehicles))
    print("First Vehicle:")
    print(json.dumps(vehicles[0].__dict__,indent=2,default=str))
  return vehicles

def __arceMultiperiod(segment: Segment, microHub: MicroHub, vehicle: Vehicle, distanceFromMicriohubToSegment: float, period: int) -> dict:
  resultArce = {}
  durationFixed     = 0       # Fixed duration for each route
  durationVariable  = 0       # Variable duration per customer of each route
  numberOfStopPerRoute    = 0    # Effective number of stop per route
  numberOfRoutePerVehicle = 0    # Number of route per vehicle by period
  fleetSize         = 0       # Fleet Size
  h                 = 0       # Stop per route accounting for capacity only
  costSetUp         = 0
  costLineHaul      = 0
  costIntraRoute    = 0
  costFirstTier     = 0
  totalCostArce     = 0

  h = vehicle.capacity / segment.dropSizeByPeriod[period]

  # fixed duration for each route : setup time + two times go and back to the segment from microhub.
  durationFixed = vehicle.timeSetupRoute + 2*distanceFromMicriohubToSegment/vehicle.speedLinehaul

  # variable duration per customer of each route
  durationVariable = (segment.localCircuity*segment.k)/(math.sqrt(segment.demandByPeriod[period])*vehicle.speedInterStop + vehicle.timeServicePerStop)

  # Effective number of stop per route
  numberOfStopPerRoute  = h if (h*durationVariable + durationFixed <= vehicle.timeServiceMaximum) else (vehicle.timeServiceMaximum - durationFixed)/durationVariable

  # Number of routes per vehicle per period
  numberOfRoutePerVehicle = vehicle.timeServiceMaximum/(h*durationVariable+durationFixed) if (h*durationVariable + durationFixed <= vehicle.timeServiceMaximum) else 1

  # Fleet Size
  fleetSize = (segment.densityPopulationByPeriod[period]*segment.areaKm)/(numberOfStopPerRoute*numberOfRoutePerVehicle)

  # Cost First Echelon based-time from DC to Microhub
  costFirstTier = microHub.costFromDC

  # Cost SetUp + Fixed
  costSetUp = vehicle.costFixed*fleetSize

  # Cost LineHaul
  costLineHaul = fleetSize*numberOfRoutePerVehicle*(2*distanceFromMicriohubToSegment*vehicle.k*vehicle.costByTime/vehicle.speedLinehaul + 2*distanceFromMicriohubToSegment*vehicle.k*vehicle.costByDistance)

  # Cost Intra Route
  costIntraRoute = fleetSize*numberOfRoutePerVehicle*numberOfStopPerRoute((vehicle.timeSetupRoute + vehicle.timeServicePerStop*segment.dropSizeByPeriod[period] + (vehicle.k*segment.k)/(math.sqrt(segment.densityPopulationByPeriod[period])*vehicle.speedInterStop))*vehicle.costByTime +  vehicle.costByDistance*(vehicle.k*segment.k)/(math.sqrt(segment.densityPopulationByPeriod[period])))

  # Total Cost Arce by unit item-demand
  totalCostArce = costLineHaul + costSetUp + costIntraRoute

  resultArce['fleetSize']     = fleetSize
  resultArce['costFirstTier'] = costFirstTier
  resultArce['costSetUp']     = costSetUp
  resultArce['costLineHaul']  = costLineHaul
  resultArce['costIntraRoute']= costIntraRoute
  resultArce['totalCostArce'] = totalCostArce/segment.demandByPeriod[period]
  return resultArce

def calculate_ARCE(segments: list[Segment], microhubs: list[MicroHub], vehicles: list[Vehicle], distance_matrix: dict[(int,int),float], periods: int, DEBUG = False) -> dict:
  ARCE = dict(
    [((s.id,m.id,v.id,t), __arceMultiperiod(s,m,v,distance_matrix[(m.id,s.id)],t)) for t in range(periods) for v in vehicles for m in microhubs for s in segments ]
  )
  
  if DEBUG:
    print("-"*50)
    print("ARCE:")
    print(json.dumps(ARCE.__dict__,indent=2,default=str))
  return ARCE