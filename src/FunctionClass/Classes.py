import numpy as np

class Segment:
  def __init__(self,
              id: int,
              x: float,y: float,
              customersByPeriod : list,
              demandByPeriod    : list,
              localCircuity     : float,
              areaKm            : float,
              k=0.57
              ):
    self.id                         = id
    self.x                          = x
    self.y                          = y
    self.location                   = (self.x,self.y)
    self.customersByPeriod          = np.array(customersByPeriod)
    self.demandByPeriod             = np.array(demandByPeriod)
    self.localCircuity              = localCircuity
    self.areaKm                     = areaKm
    self.densityPopulationByPeriod  = self.customersByPeriod/self.areaKm
    self.k                          = k # Daganzo (1994) L2 norm VRP
    self.dropSizeByPeriod           = [self.demandByPeriod[t]/self.customersByPeriod[t] for t in range(len(self.demandByPeriod))]


class MicroHub:
  """
  Description:

  Parameters:
    costOperation       : [capacity:str][periodo:int]
    capacityOperation   : [capacity:str]
  """

  def __init__(self,
              id: int,
              x: float, y: float,
              costFixed         : list[int],
              costOperation     : dict[str, list[int]],
              costInventory     : list[int],
              costFromDC        : list[int],
              capacityOperation : dict[str, int],
              capacityInventory : int,
              timeFromDC        : float,
              areaKm            : float
              ):
    self.id                 = int(id)
    self.x                  = x
    self.y                  = y
    self.location           = (self.x, self.y)
    self.costFixed          = costFixed
    self.costOperation      = costOperation
    self.costInventory      = costInventory
    self.costFromDC         = costFromDC
    self.capacityOperation  = capacityOperation
    self.capacityInventory  = capacityInventory
    self.timeFromDC         = timeFromDC
    self.areaKm             = areaKm


class Vehicle:
  def __init__(self,
              id: str,
              capacity        : int,
              costByDistance  : int,
              costByTime      : int,
              costFixed       : int,
              speedLinehaul   : float,
              timeSetupRoute  : float,
              speedInterStop  : float,
              timeServiceMaximum  : float,
              timeServicePerStop  : float,
              vehicleType="2E",
              k = 1
              ):
    self.id       = id
    self.capacity = capacity
    self.costByDistance     = costByDistance      #cd
    self.costByTime         = costByTime          #ch
    self.costFixed          = costFixed           #F
    self.speedLinehaul      = speedLinehaul       #sl 
    self.timeSetupRoute     = timeSetupRoute      #ts
    self.speedInterStop     = speedInterStop      #s
    self.timeServiceMaximum = timeServiceMaximum  #Tm
    self.timeServicePerStop = timeServicePerStop  #td
    self.k = k
    self.vehicleType = vehicleType

