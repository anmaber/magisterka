from ortools.sat.python import cp_model
import pandas as pd
import numpy as np
from IPython.display import display
import os
import time
import pulp
import copy

def readAvailibility():
    availbility = {}
    for file in os.listdir('input/enough/dataSet1'):
        data = pd.read_excel('input/enough/dataSet1/'+file, header=0,index_col=0)
        availbility.update({file[:-4] : np.array(data)}) 
    return availbility

def initScheduleFromAvailbility(availability):
    numOfWorkers = len(availability)
    allShiftsRequests = list(availability.values())
    workersNames = list(availability.keys())
    numOfShifts = len(allShiftsRequests[0][0])
    numOfDays = len(allShiftsRequests[0])

    allWorkers = range(numOfWorkers)
    allShifts = range(numOfShifts)
    allDays = range(numOfDays)

    solution = []

    for day in allDays:
        dayShifts = [None] * numOfShifts
        for shift in allShifts:
            for worker in allWorkers:
                if allShiftsRequests[worker][day][shift] == 1 and not (workersNames[worker] in dayShifts):
                    dayShifts[shift] = workersNames[worker]
                    break
        solution.append(dayShifts)

    return solution

def evaluateDay(day):
    fitnessValue =  0
    multipleShifts = len(day) - len(set(day))
    numOfEmptyShifts =  day.count(None)
    if numOfEmptyShifts > 1:
        multipleShifts -= numOfEmptyShifts - 1
    fitnessValue += numOfEmptyShifts * 10 + multipleShifts * 30
    return fitnessValue

def calculateFitness(solution):
    fitnessValue =  0
    for day in solution:
        fitnessValue += evaluateDay(day)    
    return fitnessValue

def getEvaluatedSolutions(neighbourhoodList):
    evaluatedSolutions = {}
    for solution, index in zip(neighbourhoodList, range(len(neighbourhoodList))):
        evaluatedSolutions.update({index : calculateFitness(solution)})
    
    return dict(sorted(evaluatedSolutions.items(), key=lambda item: item[1]))

def generateNeighbourhood(initialSolution, availbility):
    neighbourhood = []
    for day in range(len(initialSolution)):
        for shift in range(len(initialSolution[day])):
            for worker in availbility[day][shift]:
                if worker != initialSolution[day][shift]:
                    dayShifts = copy.deepcopy(initialSolution[day])
                    dayShifts[shift] = worker
                    moveValue = evaluateDay(dayShifts)
                    neighbourhood.append((day, shift, worker, moveValue))
    return neighbourhood
    
def convertAvailbility(availability):
    numOfWorkers = len(availability)
    allShiftsRequests = list(availability.values())
    workersNames = list(availability.keys())
    numOfShifts = len(allShiftsRequests[0][0])
    numOfDays = len(allShiftsRequests[0])
    allWorkers = range(numOfWorkers)
    allShifts = range(numOfShifts)
    allDays = range(numOfDays)

    solution = []

    for day in allDays:
        dayShifts = [None] * numOfShifts
        for shift in allShifts:
            dayShifts[shift] = []
            for worker in allWorkers:
                if allShiftsRequests[worker][day][shift] == 1:
                    dayShifts[shift].append(workersNames[worker])
        solution.append(dayShifts)
    return solution

def tabuSearch(availbility):
    convertedAvailbility = convertAvailbility(availbility)
    initialSolution = initScheduleFromAvailbility(availbility)
    bestSolution = copy.deepcopy(initialSolution)
    bestSolutionValue = calculateFitness(bestSolution)
    currentSolution = copy.deepcopy(initialSolution)
    currentSolutionValue = calculateFitness(currentSolution)
    tabuTenure = 6
    tabuList = {}
    iterations = 0
    maxIterations = 50

    while iterations < maxIterations:
        neighbours = generateNeighbourhood(currentSolution, convertedAvailbility)
        tabuSolutions = tabuList.keys()
        neighbours = list(set(neighbours) - set(tabuSolutions)) #pamietaj o mozliwosci wykorzystania rozwiazania z tabu listy
        neighbours = sorted(neighbours, key = lambda item : item[3])
        bestMove = neighbours[0]
        currentSolutionDayValue = evaluateDay(currentSolution[bestMove[0]])
        currentSolution[bestMove[0]][bestMove[1]] = bestMove[2]
        currentSolutionValue = currentSolutionValue - currentSolutionDayValue + bestMove[3]
        if currentSolutionValue < bestSolutionValue:
            bestSolution = copy.deepcopy(currentSolution)
            bestSolutionValue = copy(currentSolutionValue)

        keysToPop = []
        for key in tabuList:
            tabuList[key] -= 1
            if tabuList[key] == 0:
                keysToPop.append(key)
        
        for key in keysToPop:
            tabuList.pop(key)
        
        tabuList.update({bestMove: tabuTenure})
        iterations +=1
    return bestSolution
