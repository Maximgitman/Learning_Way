import os
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
import concurrent.futures

base_url = 'https://api.hh.ru'
vacancy_url = f"{base_url}/vacancies"
vacancies_url = f"{base_url}/vacancies"

headers = {
    'User-Agent': 'Pamagiti/1.0 (mail@bykov-alexei.ru)'
}

def parse_salary(df):
  exchange_rates = {
      'RUR': 1,
      'USD': 72.06,
      'EUR': 87.78,
      'KZT': 0.17,
      'BYR': 28.67,
  }

  new_column = df.salary.apply(lambda x: None if x is None else exchange_rates[x['currency']] * (x['from'] if x['from'] is not None else x['to']))
  return new_column

def parse_experience(df):
  if 'experience' in df:
    new_column = df['experience'].apply(lambda x: 'notSpecified' if type(x) == float else x['id'])
    return new_column
  else:
    return pd.Series(['notSpecified'] * len(df))

def parse_skills(df):
  if 'key_skills' in df:
    new_column = df.key_skills.apply(lambda x: [] if type(x) == float else [el['name'].upper() for el in x])
    return new_column
  else:
    return pd.Series([[]] * len(df))

def skill_presented(df, skill):
  mask = df.key_skills.apply(lambda x: skill in x)
  return mask

def list_skills(df):
  skills = []
  for i, row in df.iterrows():
    skills.extend(row['key_skills'])
  return pd.Series(skills)

def skills_intersection(df, skills):
  skills = set(skills)
  new_column = df.key_skills.apply(lambda x: 2 * len(set(x) & skills) / (len(x) + len(skills)))
  return new_column

def fix_skills(df):
  new_column = []
  for i, row in df.iterrows():
    skills = row['key_skills']
    if type(row['snippet']) == dict:
      for key, value in row['snippet'].items():
          for skill in all_skills:
            if value is not None and (' '+skill.lower()+' ' in value.lower() or ' '+skill.lower()+',' in value.lower() or ' '+skill.lower()+'\n' in value.lower()):
              if skill == 'С' or skill == 'с':
                skill = 'C'
              skills.append(skill.upper())
    new_column.append(list(set(skills)))
  return new_column

def get_vacancy(id=1):
  response = requests.get(f"{vacancy_url}/{id}", headers=headers)
  if response.ok:
    return response.json()
  else:
    # print(response.text)
    return response

def get_vacancies(title="Data Science"):
  # print('get_vacancies')
  # params = {
  #     'text': title,
  #     'per_page': 100,
  #     'page': 0,
  # }
  # print('1')
  # response = requests.get(vacancies_url, headers=headers, params=params)
  # print('2')
  # assert response.ok
  # data = response.json()
  # found = data['found']
  
  # result = data['items']
  # print('started')
  # def paged_get(page):
  #   params = {
  #     'text': title,
  #     'per_page': 100,
  #     'page': page,
  #   }
  #   print(page)
  #   response = requests.get(vacancies_url, headers=headers, params=params)
  #   if not response.ok:
  #     print(page, 'finished')
  #     return None
  #   else:
  #     data = response.json()
  #     vacancies = [get_vacancy(d['id']) for d in data['items']]
  #     print(page, 'finished')
  #     return vacancies

  # with concurrent.futures.ThreadPoolExecutor() as executor:
  #   futures = [executor.submit(paged_get, page) for page in range(0, 20)]
  #   results = [f.result() for f in futures]

  # print('result')
  # result = []
  # for r in results:
  #   result.extend(r)

  params = {
      'text': title,
      'per_page': 100,
      'page': 0,
  }
  response = requests.get(vacancies_url, headers=headers, params=params)
  assert response.ok
  data = response.json()
  found = data['found']
  
  result = data['items']
  while len(result) != found:
    params['page'] += 1
    print(params['page'])
    response = requests.get(vacancies_url, headers=headers, params=params)
    if not response.ok:
      return result
    data = response.json()
    # vacancies = [get_vacancy(d['id']) for d in data['items']]
    result.extend(vacancies)

  data = pd.DataFrame(result)
  data.salary = parse_salary(data)
  # data.experience = parse_experience(data)
  data.key_skills = parse_skills(data)
  data.key_skills = fix_skills(data)
  return data