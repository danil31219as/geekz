import requests
import pandas as pd
from datetime import datetime


#Создаем переменные и функции, которые используются на протяжении всего кода.
headers = {"x-auth-token":"b540bd407852678c0af5b11105dcde14", "Content-Type": "application/x-www-form-urlencoded"} 

list_of_courses = requests.get(f"https://userapi.webinar.ru/v3/organization/courses", headers=headers).json()["data"]

main_data_about_group = requests.get(f"https://userapi.webinar.ru/v3/organization/courses/groups", headers=headers).json()
del main_data_about_group[2]


#Функция создания файлов
def make_files(name_file, data):
  df = pd.DataFrame(data).drop_duplicates()
  df.to_csv(f"{name_file}.csv", sep=';', index=False, encoding="utf-8-sig"))


#Функция для упрощения запросов
def custom_requests(typee, *args):
  if typee == 0:
    return requests.get(f"https://userapi.webinar.ru/v3/courses/{args[0]}/groups/{args[1]}/statistics", headers=headers).json()
  elif typee == 1:
    return requests.get(f"https://userapi.webinar.ru/v3/contacts/{args[0]}/user", headers=headers).json()
  elif typee == 2:
    return requests.get(f"https://userapi.webinar.ru/v3/organization/users/{args[0]}/statistics", headers=headers).json()

#Создание таблицы course, в которой хранятся все возможные данные о курсах.
  
for i in list_of_courses:
  i["owner"] = i["owner"]["id"]
  
make_files("course", list_of_courses)


#Создание таблицы groups, в которой хранятся все возможные данные о группах.

colown_redact = ["startsAt", "course"]
li = []
for i in main_data_about_group:
    li.append(i.copy())
    li[-1]["id_group"] = li[-1]["id"]
    for j in colown:
        li[-1].update(i[j])
        del li[-1][j]
    li[-1]["id_course"],li[-1]["id"] = li[-1]["id"], li[-1]["id_group"]
    li[-1]["date"] = datetime.strptime(li[-1]["date"], '%Y-%m-%d %H:%M:%S.%f')
    del li[-1]["id_group"]
    
make_files("groups", li)

#Создание таблицы lessons, в которой хранятся все возможные данные о лекциях

li = []
for i in main_data_about_group:
  data_aboit_group = custom_requests(0, i['course']['id'], i['id'])[0]["lessonsPassing"]
  for j in data_aboit_group:
    li.append({"id": j["id"], "name": j["name"], "type": j["type"], "id_group": i["id"], "data":""})

make_files("lessons", li)

#Создание таблицы students, в которой хранятся все возможные данные о учениках

li = []
for i in main_data_about_group:
  data_aboit_group = custom_requests(0, i['course']['id'], i['id'])
  for j in data_aboit_group:
    userID = custom_requests(1, j['contact']['id'])["id"]
    data_about_student = custom_requests(2, userID)[0]['contact']
    li.append({"id":userID, "firstName":data_about_student["firstName"],
               "lastName":data_about_student["lastName"], "email":data_about_student["email"] })
    
make_files("students", li)

#Создание таблицы lesson_student, в которой устанавливается связь между уроками и учениками

li = []
for i in main_data_about_group:
  data_aboit_group = custom_requests(0, i['course']['id'], i['id'])
  for j in data_aboit_group:
    userID = custom_requests(1, j['contact']['id'])["id"]
    for c in j['lessonsPassing']:
      li.append({"userid":userID, "lessonid":c["id"], "date": 1 if c["date"] else 0,
                 "score": c["score"] if "score" in c else 0})
      
make_files("lesson_student", li)

#Создание таблицы user_grou, в которой устанавливается связь между группами и учениками

li = []
for i in main_data_about_group:
  data_aboit_group = custom_requests(0, i['course']['id'], i['id'])
  for j in data_aboit_group:
    userID = custom_requests(1, j['contact']['id'])["id"]
    datareg = datetime.strptime(j['student']['registeredAt']['date'], '%Y-%m-%d %H:%M:%S.%f')
    datelast = datetime.strptime(j['student']['lastActivityAt']['date'], '%Y-%m-%d %H:%M:%S.%f')
    status = j["coursePassing"]['status']
    passingProgress = j["coursePassing"]['passingProgress']
    averageScore = j["coursePassing"]['averageScore']
    li.append({"user_id":userID, "group_id":i['id'], "datereg":datareg ,
               "datelast": datelast, "status":status, "passingProgress":passingProgress, 
               "averageScore":averageScore})
    
make_files("user_grou", li)
