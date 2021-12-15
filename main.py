import datetime

import pymongo
import random


def connect():
    client = pymongo.MongoClient(
        "mongodb+srv://SMBUD:Qwer_1234@cluster0.mdv7s.mongodb.net/LastBig?retryWrites=true&w=majority")

    return client


def produceNames():
    f = open('names.txt')
    lines = f.readlines()
    names = []
    for i in lines:
        names.append(i.split(",")[0])
    authNames = ["Milano", "Turin", "Lecco", "Como"]
    vaccineName = ["Pfizer", "J&J", "Astrazeneca", "COVIran Barkat", "Razi Cov Pars"]
    return names, authNames, vaccineName


def authorizedbodies(db, names):
    auth = db.AuthorizedBodies
    authIDS = []
    types = ["Hospital", "Laboratory"]
    nameAuth = []
    counter = 1
    for i in names:
        x = random.uniform(10.5, 75.5)
        y = random.uniform(10.5, 75.5)
        t = types[random.randint(0, types.__len__() - 1)]
        name = i + " " + t
        nameAuth.append(name)
        author = {
            "_id": counter,
            "GPS": str(x) + "," + str(y),
            "Name": name,
            "Type": t,
            "Add": "WW",
            "Depart": "EE"
        }
        authIDS.append(auth.insert_one(author).inserted_id)
        counter = counter + 1
    print(nameAuth)
    print(authIDS)
    return authIDS


def vaccination(db, vaccineName, authrozedBodies):
    vac = db.Vaccines
    year = random.randint(2018, 2021)
    month = random.randint(1, 10)
    day = random.randint(1, 28)
    vaccine = {
        "Place": "Room" + str(random.randint(1,10)),
        "Brand": vaccineName[random.randint(0, vaccineName.__len__() - 1)],
        "Type": "XX",
        "Iot": "WW",
        "PDate": datetime.datetime(year, month, day),
        "InjectionDate": datetime.datetime(year, month + 1, day),
        "D/N": "Doctor1",
        "Auth": authrozedBodies[random.randint(0, authrozedBodies.__len__() - 1)]
    }
    vac.insert_one(vaccine)
    return vaccine


def vaccination2(db, vaccineName, authrozedBodies, vac1):
    vac = db.Vaccines

    vaccine = {
        "Place": "Room" + str(random.randint(1, 10)),
        "Brand": vaccineName[random.randint(0, vaccineName.__len__() - 1)],
        "Type": "XX",
        "Iot": "WW",
        "PDate": datetime.datetime(vac1["PDate"].year, vac1["PDate"].month + 1, vac1["PDate"].day),
        "InjectionDate": datetime.datetime(vac1["InjectionDate"].year, vac1["InjectionDate"].month + 1,
                                           vac1["InjectionDate"].day),
        "D/N": "Doctor1",
        "Auth": authrozedBodies[random.randint(0, authrozedBodies.__len__() - 1)]
    }
    vac.insert_one(vaccine)
    return vaccine




def testCovid(db, authrozedBodies):
    testCol = db.Tests
    res = ["Pos", "Neg"]
    year = random.randint(2018, 2021)
    month = random.randint(1, 11)
    day = random.randint(1, 28)
    test = {
        "Result": res[random.randint(0, 1)],
        "Date": datetime.datetime(year, month, day),
        "Place": "Hospital",
        "D/N": "Nurse1",
        "Auth": authrozedBodies[random.randint(0, authrozedBodies.__len__() - 1)]
    }
    testCol.insert_one(test)
    return test


def validationRules(db, vaccineNames):
    valid = db.Validities
    for i in vaccineNames:
        rule = {
            "Brand": i,
            "Validity": [random.randint(1, 3), random.randint(3, 6), random.randint(6, 9)]
        }
        valid.insert_one(rule)


def findID(names, ids, nameOfInterest):
    if nameOfInterest in names:
        return ids[names.index(nameOfInterest)]
    else:
        print("No name available")

if __name__ == '__main__':
    client = connect()
    db = client.LastBig
    names, authnames, vaccineName = produceNames()
    validationRules(db, vaccineName)
    authIDs = authorizedbodies(db, authnames)
    persons = db.People
    for i in range(0, 300):
        vaccineObj = vaccination(db, vaccineName, authIDs)
        testObj = testCovid(db, authIDs)
        if random.randint(1, 10) > 7:
            person = {
                "Name": names[i],
                "Vaccines": [
                    vaccineObj
                             ],
                "Tests": [
                    testObj
                ],
                "ContactInfo": "+39123456",
                "EmergencyContactInfo": {
                    "Name": names[random.randint(0, names.__len__() - 1)],
                    "ContactInfo": "+39654789"
                },
                "Demographic": "YY"
            }
            res = persons.insert_one(person).inserted_id
        else:
            vaccineObj2 = vaccination2(db, vaccineName, authIDs, vaccineObj)
            person = {
                "Name": names[i],
                "Vaccines": [
                    vaccineObj, vaccineObj2
                ],
                "Tests": [
                    testObj
                ],
                "ContactInfo": "+39123456",
                "EmergencyContactInfo": {
                    "Name": names[random.randint(0, names.__len__() - 1)],
                    "ContactInfo": "+39654789"
                },
                "Demographic": "YY"
            }
            res = persons.insert_one(person).inserted_id
