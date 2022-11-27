from ortools.sat.python import cp_model
import pandas as pd
import numpy as np
from IPython.display import display
import os
import time

def readAvailibility():
    availbility = {}
    for file in os.listdir('dyspo'):
        data = pd.read_excel('dyspo/'+file, header=0,index_col=0)
        availbility.update({file[:-4] : np.array(data)}) 
        print(availbility)
    return availbility

def saveSchedule(schedule):

    numOfShifts = len(schedule[0])
    colNames = []
    for i in range(numOfShifts):
        colNames.append("Zmiana " + str(i))
    
    df = pd.DataFrame(schedule, columns = colNames)
    df.to_excel("grafik/grafik.xls")

def countEmptyShifts(schedule):
    numOfEmptyShifts = 0
    for day in schedule:
        for shift in day:
            if shift == None:
                numOfEmptyShifts +=1
    return numOfEmptyShifts

def getNumOfDaysWithAvailbility(personalAvailbility):
    numOfDaysWithAvailbility = 0
    for day in personalAvailbility:
        for request in day:
            if request != 0:
                numOfDaysWithAvailbility +=1
                break
    return numOfDaysWithAvailbility


def getDifferenceAvailbilityAndSchedule(availbility, schedule):
    numOfWorkers = len(availbility)
    allShiftsRequests = list(availbility.values())
    workersNames = list(availbility.keys())

    diff = {}
    for name in workersNames:
        diff[name] = getNumOfDaysWithAvailbility(availbility[name])

    for day in schedule:
        for shift in day:
            if shift != None:
                diff[shift] -= 1
    print(diff)


def createScheduleWithConstraintProgramming(availability):
    print("cp")
    numOfWorkers = len(availability)
    allShiftsRequests = list(availability.values())
    workersNames = list(availability.keys())
    numOfShifts = len(allShiftsRequests[0][0])
    numOfDays = len(allShiftsRequests[0])
    print('num of woekers: ', numOfWorkers, ' numOfshifts ', numOfShifts, ' numOfDays ', numOfDays)
    allWorkers = range(numOfWorkers)
    allShifts = range(numOfShifts)
    allDays = range(numOfDays)
 # Creates the model.
    model = cp_model.CpModel()

    # Tworzenie zmian
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in allWorkers:
        for d in allDays:
            for s in allShifts:
                shifts[(n, d,
                        s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))

    # Kazda zmiana jest przypisana max do jednej osoby (możliwość pustych zmian)
    for d in allDays:
        for s in allShifts:
            model.AddAtMostOne(shifts[(n, d, s)] for n in allWorkers)

    # Kazdy pracownik moze byc przypisany do maksymalnie jednej zmiany w ciągu dnia
    for n in allWorkers:
        for d in allDays:
            model.AddAtMostOne(shifts[(n, d, s)] for s in allShifts)

    #zapewniamy ze zmiany zostana przypisane tylko wtedy gdy byla wyrazona dyspozycyjnosc
    for n in allWorkers:
        for d in allDays:
            for s in allShifts:
                model.Add(shifts[(n, d, s)] <= allShiftsRequests[n][d][s])

    #maxymalizujmy liczbe wypełnionych zmian 
    model.Maximize(
        sum(shifts[(n, d, s)] for n in allWorkers
            for d in allDays for s in allShifts))
    
    #proba rozlozenia zmian
    # for n in allWorkers:
    #     num_shifts_worked = []
    #     num_shifts_requested = []
    #     for d in allDays:
    #         for s in allShifts:
    #             num_shifts_worked.append(shifts[(n,d,s)])
    #             num_shifts_requested.append(shift_requests[n][d][s])
    #     model.Minimize(sum(num_shifts_requested)-sum(num_shifts_worked))

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution = []

    if status == cp_model.OPTIMAL:
        print('Solution:')
        for d in allDays:
            print('Day', d)
            dayShifts = [None] * numOfShifts
            for shift in allShifts:
                for worker in allWorkers:
                    if solver.Value(shifts[(worker, d, shift)]) == 1:
                        dayShifts[shift] = workersNames[worker]
            solution.append(dayShifts)
                    
            for n in allWorkers:
                for s in allShifts:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        if allShiftsRequests[n][d][s] == 1:
                            print('Nurse', n+1, 'works shift', s, '(requested).')
                        else:
                            print('Nurse', n+1, 'works shift', s,
                                  '(not requested).')
            print()

    else:
        print('No optimal solution found !')


    # Statistics.
    print('\nStatistics')
    print('  - conflicts: %i' % solver.NumConflicts())
    print('  - branches : %i' % solver.NumBranches())
    print('  - wall time: %f s' % solver.WallTime())
    
    return solution


def main():
    availbility = readAvailibility()
    start = time.time()
    schedule = createScheduleWithConstraintProgramming(availbility)
    end = time.time()
    duration = end - start
    print("elapsed time: " + str(duration) + " Num of empty shifts: " + str(countEmptyShifts(schedule)))
    saveSchedule(schedule)
    getDifferenceAvailbilityAndSchedule(availbility,schedule)
   
if __name__ == '__main__':
    main()