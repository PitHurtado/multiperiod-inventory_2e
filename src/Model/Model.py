#import gurobipy as gp
#from gurobipy import GRB, quicksum
from FunctionClass.Classes import Segment, MicroHub, Vehicle

class MP_2E:
  __statusRunning = { 1:"LOADED",
              2:"OPTIMAL",
              3:"INFEASIBLE",
              4:"INF_OR_UNBD",
              5:"UNBOUNDED",
              6:"CUTOFF",
              7:"ITERATION_LIMIT",
              8:"NODE_LIMIT",
              9:"TIME_LIMIT",
              10:"SOLUTION_LIMIT",
              11:"INTERRUPTED",
              12:"NUMERIC",
              13:"SUBOPTIMAL",
              14:"INPROGRESS",
              15:"USER_OBJ_LIMIT",
              16:"WORK_LIMIT"}

  def __init__(self, arce: dict, nameModel = "Deterministic"):
    self.model = gp.Model(nameModel)

    self.X  = {}  # asignacion de MH a Seg
    self.Y  = {}  # apertura de MH
    self.W  = {}  # operacion de MH
    self.Z  = {}  # cantidad enviada de MH a Seg
    self.I  = {}  # inventario de MH
    self.R  = {}  # cantidad enviada de DC a MH
    
    self.arce       = arce 
    self.objective  = {}
    self.metrics    = {}

  def build(self, periods: int, segments: list[Segment], microHubs: list[MicroHub], vehicles: list[Vehicle]):
    self.model.reset()
    # Varaibles
    self.addVariables(periods, segments, microHubs, vehicles)
    # Objetive
    self.addObjetive(periods, segments, microHubs, vehicles)
    # Constraints
    self.__addConst_OpenMH(periods, microHubs)
    self.__addConst_OperationMH(periods, microHubs)
    self.__addConst_CapacityOperationMH(periods, microHubs)
    self.__addConst_BalanceMH(periods, segments, microHubs, vehicles)
    self.__addConst_DeliveryToSegment(periods, segments, microHubs, vehicles)
    self.__addConst_SegmentAssignment(periods, segments, microHubs)
    self.__addConstr_AssignmentOperationMH(periods, segments, microHubs)
    self.__addConstr_CapacityInventoryMH(periods, microHubs)

  def __addVariables(self, periods: int, segments: list[Segment], microHubs: list[MicroHub], vehicles: list[Vehicle]):
    self.X  = dict(
      [((m.id,s.id,t),self.model.addVar(vtype=GRB.BINARY, name="X_m%s_s%s_t%s" %(m.id,s.id,t))) for t in range(periods) for m in microHubs for s in segments]
    )
    self.W  = dict(
      [((m.id,q,t),self.model.addVar(vtype=GRB.BINARY, name="W_m%s_a%s_t%s" %(m.id,q,t))) for t in range(periods) for m in microHubs for q in m.capacityOperation.keys()]
    )
    self.Y  = dict(
      [((m.id,t),self.model.addVar(vtype=GBR.BINARY, name="Y_m%s_t%s") %(m.id,t)) for t in range(periods) for m in microHubs]
    )
    self.Z  = dict(
      [((m.id,s.id,v.id,t),self.model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name="Z_m%s_s%s_v%s_t%s" %(m.id,s.id,v.id,t))) for t in range(periods) for s in segments for m in microHubs for v in vehicles]
    )
    self.R  = dict(
      [((m.id,t),self.model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name="R_m%s_t%s" %(m.id,t))) for t in range(periods) for m in microHubs]
    )
    self.I  = dict(
      [((m.id,t),self.model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name="I_m%s_t%s" %(m.id,t))) for t in range(periods) for m in microHubs]
    )

  def __addObjetive(self, periods: int, segments: list[Segment], microHubs: list[MicroHub], vehicles: list[Vehicle]):
    costFixed = quicksum(
      [m.costFixed[t]*self.Y[(m.id,t)] for t in range(periods) for m in  microHubs]
    )

    costOperation = quicksum(
      [m.costOperation[q][t]*self.W[(m.id,q,t)] for t in range(periods) for m in microHubs for q in m.capacityOperation.keys()]
    )

    costInventory = quicksum(
      [m.costInventory[t]*self.I[(m.id,t)] for t in range(periods) for m in microHubs]
    )

    cost_1e = quicksum(
      [m.costFromDC[t]*self.R[(m.id,t)]  for t in range(periods) for m in microHubs]
    )

    cost_2e = quicksum(
      [self.arce[(s.id,m.id,v.id,t)]["totalCostArce"]*self.Z[(s.id,m.id,v.id,t)] for t in range(periods) for s in segments for m in microHubs for v in vehicles]
    )

    costo_total = costFixed + costOperation + costInventory + cost_1e + cost_2e

    self.model.setObjective(costo_total, GRB.MINIMIZE)

  def __addConst_OpenMH(self, periods: int, microHubs: list[MicroHub]):
    for m in microHubs:
      nameConstraint = "R_Open_m"+str(m.id)
      self.model.addConstr(
        quicksum(
          [self.Y[(m.id,t)] for t in range(periods)]
          ) 
        <= 1
        , name=nameConstraint)

  def __addConst_OperationMH(self, periods: int, microHubs: list[MicroHub]):
    for t in range(periods):
      for m in microHubs:
        nameConstraint  = "R_Operation_m"+str(m.id)+"_t"+str(t)
        self.model.addConstr(
          quicksum(
            [self.W[(m.id,q,t)] for q in m.capacityOperation.keys()] 
            ) 
          <= 
          quicksum(
            [self.Y[(m.id,k)] for k in range(t+1)]
            ) 
          , name=nameConstraint
        )

  def __addConst_CapacityOperationMH(self, periods: int, microHubs:  list[MicroHub]):
    for t in range(periods):
      for m in microHubs:
        nameConstraint = "R_CapacityOperation_m"+str(m.id)+"_t"+str(t)
        self.model.addConstr(
          self.R[(m.id,t)]
          <= 
          quicksum(
            [m.capacityOperation[q]*self.W[(m.id,q,t)] for q in m.capacityOperation.keys()]
            )
          , name=nameConstraint
        )

  def __addConst_BalanceMH(self, periods: int, segments: list[Segment], microHubs: list[MicroHub], vehicles: list[Vehicle]):
    for m in microHubs:
      nameConstraint = "R_Balance_m"+str(m.id)+"_t0"
      self.model.addConstr(
        self.R[(m.id,0)] - self.I[(m.id,1)]
        ==
        quicksum(
          [self.Z[(m.id,s.id,v.id,0)] for s in segments for v in vehicles]
        )
        , name=nameConstraint
      )
      for t in range(1,periods):
        for m in microHubs:
          nameConstraint = "R_Balance_m"+str(m.id)+"_t"+str(t)
          self.model.addConstr(
            self.R[(m.id,t)] + self.I[(m.id,t)] - self.I[(m.id,t-1)]
            ==
            quicksum(
              [self.Z[(m.id,s.id,v.id,t)] for s in segments for v in vehicles]
            )
            , name=nameConstraint
          )

  def __addConst_DeliveryToSegment(self, periods: int, segments: list[Segment], microhubs: list[MicroHub], vehicles: list[Vehicle]):
    for t in periods:
      for s in segments:
        for m in microhubs:
          nameConstraint = "R_DeliveryToSegment_m"+str(m.id)+"_s"+str(s.id)+"_t"+str(t)
          self.model.addConstr(
            quicksum(
              [self.Z[(m.id,s.id,v.id,t)] for v in vehicles]
            ) 
            == 
            s.demandByPeriod[t]*self.X[(m.id,s.id,t)] 
            , name=nameConstraint
          )

  def __addConst_SegmentAssignment(self, periods: int, segments: list[Segment], microHubs: list[MicroHub]):
    for t in periods:
      for s in segments:
        nameConstraint = "R_SegmentAssignment_s"+str(s.id)+"_t"+str(t)
        self.model.addConstr(
          quicksum(
            [self.X[(m.id,s.id,t)] for m in microHubs]
          )
          == 1
          , name=nameConstraint
        )

  def __addConstr_AssignmentOperationMH(self, periods: int, segments: list[Segment], microHubs: list[MicroHub]):
    for t in periods:
      for m in microHubs:
        for s in segments:
          nameConstraint = "R_AssignmentOperacion_s"+str(s.id)+"_m"+str(m.id)+"_t"+str(t)
          self.model.addConstr(
            self.X[(m.id,s.id,t)]
            <=
            quicksum(
              [self.W[(m.id,q,t)] for q in m.capacityOperation.keys()]
            )
            , name=nameConstraint
          )

  def __addConstr_CapacityInventoryMH(self, periods: int, microHubs: list[MicroHub]):
    for t in periods:
      for m in microHubs:
        nameConstraint = "R_CapacityInventory_m"+str(m.id)+"_t"+str(t)
        self.model.addConstr(
          self.I[(m.id,t)]
          <=
          quicksum(
            [self.W[(m.id,q,t)]*m.capacityInventory for q in m.capacityOperation.keys()]
          )
          , name=nameConstraint
        )

  def optimizeModel(self) -> str:
    self.model.optimize()
    return self.model.Status

  def getBreakDownObjective(self, periods: int, segments: list[Segment], microHubs: list[MicroHub], vehicles: list[Vehicle]) -> dict:
    self.objective["costFixed"] = sum(
      [m.costFixed[t]*self.Y[(m.id,t)].x for t in range(periods) for m in  microHubs]
    )
    self.objective["costOperation"] = sum(
      [m.costOperation[q][t]*self.W[(m.id,q,t)].x for t in range(periods) for m in microHubs for q in m.capacityOperation.keys()]
    )
    self.objective["costInventory"] = sum(
      [m.costInventory[t]*self.I[(m.id,t)].x for t in range(periods) for m in microHubs]
    )

    self.objective["cost_1e"] = sum(
      [m.costFromDC[t]*self.R[(m.id,t)].x  for t in range(periods) for m in microHubs]
    )

    self.objective["cost_2e"] = sum(
      [self.arce[(s.id,m.id,v.id,t)]["totalCostArce"]*self.Z[(s.id,m.id,v.id,t)].x for t in range(periods) for s in segments for m in microHubs for v in vehicles]
    )

    self.objective["objetiveFunction"] = self.model.getObjective().getValue()
    return self.objective

  def obtainMetrics(self, periods: int, segments: list[Segment], microHubs: list[MicroHub]) -> dict:
    self.metrics["gap"] = self.model.MIPGap
    return self.metrics
    
  def showModel(self):
    self.model.display()

  def setParams(self, params: dict):
    self.model.reset()
    for key, item in params.items():
      self.model.setParam(key,item)