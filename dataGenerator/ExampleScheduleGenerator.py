import pandas as pd
import numpy as np
import os
import random
import copy

class ExampleSchedulesGenerator:
    def __init__(self, numOfSchedules, workers, numOfShifts = 3, numOfDays = 7):
        self.numOfSchedules = numOfSchedules
        self.workers = workers
        self.numOfShifts = numOfShifts
        self.numOfDays = numOfDays
    
    def printSchedulesGenerator(self):
        print("Schedules generator: num of schedules:  "+ str(self.numOfSchedules))

    def generateSchedule(self):
        if len(self.workers) > self.numOfShifts:
            schedule = []
            for day in range(self.numOfDays):
                dayShifts = []
                tmpWorkers = copy.deepcopy(self.workers)
                for shifts in range(self.numOfShifts):
                    chosenWorker = random.choice(tmpWorkers)
                    tmpWorkers.remove(chosenWorker)
                    dayShifts.append(chosenWorker)
                schedule.append(dayShifts)
            # print(schedule)
            return schedule
        else :
            print("To few workers to generate schedule")
            return []

    def saveToExcel(self, schedule, scheduleIndex, path):
        numOfShifts = len(schedule[0])
        colNames = []
        for i in range(numOfShifts):
            colNames.append("Zmiana " + str(i))
        
        df = pd.DataFrame(schedule, columns = colNames)
        df.to_excel(path + "/schedule" + str(scheduleIndex) + ".xls")

    def generateScheduleWithEmptyShifts(self, schedule):
        withEmptyShifts = copy.deepcopy(schedule)
        for day in withEmptyShifts:
            numOfEmptyShifts = random.randrange(0, self.numOfShifts)
            indexes = list(range(self.numOfShifts))
            for i in range(numOfEmptyShifts):
                indexToRemove = random.choice(indexes)
                day[indexToRemove] = None
                indexes.remove(indexToRemove)

        return withEmptyShifts    

    def generateSchedules(self):
        path = "ExampleSchedules/" + "P" + str(len(self.workers)) +  "D" + str(self.numOfDays)
        emptyShiftsPath = "ExampleScheduleswithEmptyShifts/"+ "P" + str(len(self.workers)) +  "D" + str(self.numOfDays)
        if not os.path.exists(path):
                os.makedirs(path)
        
        if not os.path.exists(emptyShiftsPath):
                os.makedirs(emptyShiftsPath)

        for i in range(self.numOfSchedules):
            schedule = self.generateSchedule()
            self.saveToExcel(schedule, i, path)
            withEmptyShifts = self.generateScheduleWithEmptyShifts(schedule)
            self.saveToExcel(withEmptyShifts, i, emptyShiftsPath )

class AvailbilityGenerator():
    def __init__(self) -> None:
        self.options = ["enough", "tooFew", "redundant"]

    def readSchedule(self, srcPath):
        schedule = pd.read_excel(srcPath, header=0,index_col=0,  na_filter = False)
        print(schedule)
        return np.array(schedule)
    
    def saveAvailbilityToFiles(self, availbility, workers, destPath, index):
        numOfDays = len(availbility)
        numOfShifts = len(availbility[0])
        colNames = []
        for i in range(numOfShifts):
            colNames.append("Zmiana " + str(i))
        
        # df = pd.DataFrame(schedule, columns = colNames)
        # df.to_excel(path + "/schedule" + str(scheduleIndex) + ".xls")

        for worker in workers:
            availbilityToSave = []
            for day in availbility:
                dayAvailbility = []
                for shift in day:
                    if worker in shift:
                        dayAvailbility.append(1)
                    else:
                        dayAvailbility.append(0)
                availbilityToSave.append(dayAvailbility)
            df = pd.DataFrame(availbilityToSave, columns = colNames)
            pathDir = destPath + "/dataSet" +str(index)
            
            path = pathDir+ "/" + str(worker) + ".xls"
            if not os.path.exists(pathDir):
                os.makedirs(pathDir)
            df.to_excel(path)



    def generateAvailbility(self,lowerBound, upperBound, destPath, srcPath ="ExampleSchedules"):
        idx = 0
        for file in os.listdir(srcPath):
            exampleSchedule = self.readSchedule(srcPath+"/"+file)
            availbility = []
            numOfDays = len(exampleSchedule)
            numOfShifts = len(exampleSchedule[0])
            workers = []
            for day, dayIdx in zip(exampleSchedule, range(numOfDays)):
                availbilityDay = [list()] * numOfShifts
                for shift, shiftIdx in zip(day, range(numOfShifts)):
                    if (not shift in workers) and shift != '':
                        workers.append(shift)
                    availbilityDay[shiftIdx] = [shift]
                availbility.append(availbilityDay)

            if lowerBound != 0:
                lowerBound = int(len(workers)/2)
                upperBound = len(workers)
            if lowerBound == 0 and upperBound >1:
                upperBound = int(len(workers)/2)
            
            for day in availbility:
                workersToAdd = []
                numOfAdditionalWorkers = random.choice(range(lowerBound,upperBound,1)) 
                for i in range(numOfAdditionalWorkers):
                    workersToAdd.append(random.choice(workers))
                for worker in workersToAdd:
                    shift = random.choice(day)
                    if shift[0] != '':
                        shift.append(worker)
            
            print(availbility)
            print(file)
            print(idx)
            self.saveAvailbilityToFiles(availbility, workers, destPath, idx)
            idx+=1    
                
        return []

    def generateAvailbilitySets(self):
        for dir in os.listdir("ExampleSchedules"):
            for option in self.options:
                if option == "tooFew":
                    self.generateAvailbility(0, 1,"ExampleAvalbility/"+dir+ "/"+option, "ExampleScheduleswithEmptyShifts/"+dir)
                elif option == "enough" :
                    self.generateAvailbility(0,2,"ExampleAvalbility/"+dir+ "/"+option, "ExampleSchedules/"+dir)
                else:
                    self.generateAvailbility(1,2,"ExampleAvalbility/"+dir+ "/"+option,"ExampleSchedules/"+dir)

def main():
    workers= ["w1", "w2","w3", "w4","w5", "w6", "w7"]
    generator = ExampleSchedulesGenerator(3,workers, 3, 30)
    generator.generateSchedules()

    generator2 = ExampleSchedulesGenerator(3,workers, 3, 14)
    generator2.generateSchedules()

    generator3 = ExampleSchedulesGenerator(3,workers, 3, 7)
    generator3.generateSchedules()

    workers2= ["w1", "w2","w3", "w4"]
    workers3= ["w1", "w2","w3", "w4","w5", "w6", "w7","w8", "w9", "w10"]

    generator4 = ExampleSchedulesGenerator(3,workers2, 3, 14)
    generator4.generateSchedules()

    generator5 = ExampleSchedulesGenerator(3,workers3, 3, 14)
    generator5.generateSchedules()

    aGen = AvailbilityGenerator()
    aGen.generateAvailbilitySets()

if __name__ == '__main__':
    main()