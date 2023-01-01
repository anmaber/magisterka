from ortools.sat.python import cp_model
import pandas as pd
import numpy as np
from IPython.display import display
from tabu import tabuSearch
import os
import time
import pulp

class TestRunner:
    def __init__(self, numOfRepetitions, createSchedule, destination):
        self.numOfRepetitions = numOfRepetitions
        self.createSchedule = createSchedule
        self.destination = "results/" + destination +"/"
    
    def printTestRunner(self):
        print("TestRunner num of repetitions: " + str(self.numOfRepetitions)+" algo: " + self.destination)

    def readAvailibility(self, path):
        availbility = {}
        for file in os.listdir(path):
            data = pd.read_excel(path+file, header=0,index_col=0)
            availbility.update({file[:-4] : np.array(data)}) 
        return availbility

    def saveSchedule(self, schedule, path):

        numOfShifts = len(schedule[0])
        colNames = []
        for i in range(numOfShifts):
            colNames.append("Zmiana " + str(i))
        
        df = pd.DataFrame(schedule, columns = colNames)
        destPath = self.destination+path
        if not os.path.exists(destPath):
                os.makedirs(destPath)
        df.to_excel(destPath+"/grafik.xls")

    def countEmptyShifts(self, schedule):
        numOfEmptyShifts = 0
        for day in schedule:
            for shift in day:
                if shift == None:
                    numOfEmptyShifts +=1
        return numOfEmptyShifts

    def getNumOfDaysWithAvailbility(self, personalAvailbility):
        numOfDaysWithAvailbility = 0
        for day in personalAvailbility:
            for request in day:
                if request != 0:
                    numOfDaysWithAvailbility +=1
                    break
        return numOfDaysWithAvailbility


    def getDifferenceAvailbilityAndSchedule(self, availbility, schedule):
        numOfWorkers = len(availbility)
        allShiftsRequests = list(availbility.values())
        workersNames = list(availbility.keys())

        diff = {}
        for name in workersNames:
            diff[name] = self.getNumOfDaysWithAvailbility(availbility[name])

        for day in schedule:
            for shift in day:
                if shift != None:
                    diff[shift] -= 1
        print(diff)

    def runTest(self, path):
        durations = []
        numOfEmptyShiftsArr = []
        for i in range(self.numOfRepetitions):
            availbility = self.readAvailibility("input/"+ path + "/")
            start = time.time()
            schedule = self.createSchedule(availbility)
            end = time.time()
            duration = end - start
            emptyShifts = self.countEmptyShifts(schedule)
            print("elapsed time: " + str(duration) + " Num of empty shifts: " + str(emptyShifts))
            self.saveSchedule(schedule, path)            
            self.getDifferenceAvailbilityAndSchedule(availbility,schedule)
            durations.append(duration)
            numOfEmptyShiftsArr.append(emptyShifts)
        return (durations, numOfEmptyShiftsArr)
            
    
    def runTests(self):
        for workersDaysDir in os.listdir("input"):
            for option in os.listdir("input/"+ workersDaysDir):
                optionTimes = []
                optionQuality = []
                for dataSet in os.listdir("input/"+ workersDaysDir+ "/"+option):
                    print("input/"+ workersDaysDir+ "/"+option + "/" + dataSet)
                    results = self.runTest(workersDaysDir+ "/"+option+ "/" + dataSet)
                    optionTimes.append(results[0])
                    optionQuality.append(results[1])
                colnames = list(range(self.numOfRepetitions))
                rownames = list(os.listdir("input/"+ workersDaysDir+ "/"+option))
                df = pd.DataFrame(optionTimes, columns = colnames, index= rownames)
                df = df.T
                df.to_excel(self.destination + workersDaysDir+ "/"+option+"/time.xls")
                df2 = pd.DataFrame(optionQuality, columns = colnames, index= rownames)
                df2 = df2.T
                df2.to_excel(self.destination+ workersDaysDir+ "/"+option+"/quality.xls")



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
        # print('Solution:')
        for d in allDays:
            # print('Day', d)
            dayShifts = [None] * numOfShifts
            for shift in allShifts:
                for worker in allWorkers:
                    if solver.Value(shifts[(worker, d, shift)]) == 1:
                        dayShifts[shift] = workersNames[worker]
            solution.append(dayShifts)
                    
            # for n in allWorkers:
            #     for s in allShifts:
            #         if solver.Value(shifts[(n, d, s)]) == 1:
            #             if allShiftsRequests[n][d][s] == 1:
            #                 print('Nurse', n+1, 'works shift', s, '(requested).')
            #             else:
            #                 print('Nurse', n+1, 'works shift', s,
            #                       '(not requested).')
            # print()

    else:
        print('No optimal solution found !')


    # Statistics.
    # print('\nStatistics')
    # print('  - conflicts: %i' % solver.NumConflicts())
    # print('  - branches : %i' % solver.NumBranches())
    # print('  - wall time: %f s' % solver.WallTime())
    
    return solution

def createScheduleWithLinearProgramming(availability):
    print("lp")
    numOfWorkers = len(availability)
    allShiftsRequests = list(availability.values())
    workersNames = list(availability.keys())
    numOfShifts = len(allShiftsRequests[0][0])
    numOfDays = len(allShiftsRequests[0])
    print('num of woekers: ', numOfWorkers, ' numOfshifts ', numOfShifts, ' numOfDays ', numOfDays)
    allWorkers = range(numOfWorkers)
    allShifts = range(numOfShifts)
    allDays = range(numOfDays)

    var = pulp.LpVariable.dicts('VAR', (range(numOfWorkers), range(numOfDays), range(numOfShifts)), 0, 1, 'Binary')
    
    obj = None
    for worker in allWorkers:
        for day in allDays:
            for shift in allShifts:
                obj += allShiftsRequests[worker][day][shift] * var[worker][day][shift]

    problem = pulp.LpProblem('shift', pulp.LpMaximize)

    problem += obj

    for day in allDays:
        for shift in allShifts:
            c = None
            for worker in allWorkers:
                c += var[worker][day][shift]
            problem += c <= 1

    for worker in allWorkers:
        for day in allDays:
            c = None
            for shift in allShifts:
                c+= var[worker][day][shift]
            problem += c <= 1  

    status = problem.solve()
    print("Status", pulp.LpStatus[status])

    solution = []

    for d in allDays:
        dayShifts = [None] * numOfShifts
        for shift in allShifts:
            for worker in allWorkers:
                if var[worker][d][shift].value() > 0.0:
                    dayShifts[shift] = workersNames[worker]
        solution.append(dayShifts)

    # print(solution)
    return solution

def main():
    
    t = TestRunner(4, createScheduleWithConstraintProgramming, "cp")
    t.printTestRunner()
    t.runTests()

    t2 = TestRunner(4, createScheduleWithLinearProgramming, "lp")
    t2.printTestRunner()
    t2.runTests()

    t3 = TestRunner(4, tabuSearch, "tabu")
    t3.printTestRunner()
    t3.runTests()
   
if __name__ == '__main__':
    main()