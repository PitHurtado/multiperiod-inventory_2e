# README.md

@author: P. Hurtado-Cayo, J. Pina-Pardo

## Install dependences:
Run:
```
conda create <name_conda_enviroment> --file requirements.txt
```
Pre-requistite:

- license gurobi
- gurobi installed

# MultiPeriod two-echelon with Inventory Problem
### Class Segment
This class has the following parameters:

- id (int)
- geographyLocation (float, float)
- customerByPeriod (list) [customer]
- demandByPeriod (list) [item]
- localCircuity (float) [km/hr]
- areaKm (float) [km]
- densityPopulationByPeriod (list) $\frac{demandByPeriod}{areaKm}$ [item/km]
- dropSizeByPeriod (list) $\frac{demandByPeriod}{customerByPeriod}$ [item/customer]
- k (float) 

### Class MicroHub
This class has the following parameters:

- id (int)
- geographyLocation (float, float)
- capacityOperation (dict(str, int)): It depends of capacity $a$ with which MicroHub $m$ is operating [item]
- capacityInventory (int) [unit]
- costFixed (list): It depends of period $t$ the MicroHub $m$ is installed [$]
- costOperation (dict(str, list)): It depends of capacity $a$ in period $t$ the MicroHub $m$ is operating [$]
- costInventory (list): It depends of in what period $t$ the MicroHub $m$ will store items [$/item]
- costoFromDC (list) [$/items]
- timeFromDC (float) [hr]

### Class Vehicle
This class has the following parameters:

- id (int)
- vechileType (str)
- capacity (int) [item]
- costByDistance (int) [$/km]
- costByTime (int) [$/hr]
- costFixed (int) [$]
- speedLineHaul (float) [km/hr]
- speedInterStop (float) [km/hr]
- timeSetupRoute (float) [hr]
- timeServicePerStop (float) [hr]
- timeServiceMaximum (float) [hr]
- k (float)

## Description problem:


## Strategy solution

