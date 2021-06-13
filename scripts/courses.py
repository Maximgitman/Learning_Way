import sys
import time
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

sys.path.insert(0,'/usr/lib/chromium-browser/chromedriver')

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

from tensorflow.keras.preprocessing.text import Tokenizer
from scipy.spatial.distance import cosine

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('chromedriver',chrome_options=chrome_options)

def calculate_distance(skills, user_skills):
    cos_dist = []
    for s in skills:
        cos_dist.append(cosine(user_skills, s))
    cos_dist = np.array(cos_dist)
    return cos_dist

def get_actual_vacancy(vacancy_data, user_data):
    skills = vacancy_data['key_skills'].copy()

    # токенизация навыков
    tokenizer = Tokenizer(num_words=400)
    tokenizer.fit_on_texts(skills)

    bow_skills = tokenizer.texts_to_matrix(skills)
    user_skills = list(user_data['skills'].keys())
    bow_user_skills = tokenizer.texts_to_matrix([user_skills])

    # расчет косинусного расстояния навыков пользователя до навыков вакансий
    cos_dist = calculate_distance(bow_skills, bow_user_skills)

    # выбор актуальных вакансий
    actual_vacancy = vacancy_data.iloc[np.argsort(cos_dist)[:5]]

    return actual_vacancy



def find_coursera_courses(driver, query, page=1, level=1):
    """
    level - 1, 2, 3 (Beginner, Intermediate, Advanced)
    """

    level = {0: 'Beginner', 1: 'Intermediate', 2: 'Advanced', 3: 'Advanced'}[level]

    if page == 1:
        driver.get(f'https://ru.coursera.org/search?query={query}&entityTypeDescription=Courses&index=prod_all_products_term_optimization&productDifficultyLevel={level}&allLanguages=Russian')
    else:
        driver.get(f'https://ru.coursera.org/search?query={query}&entityTypeDescription=Courses&page={page}&index=prod_all_products_term_optimization&productDifficultyLevel={level}&allLanguages=Russian')
    time.sleep(2)
    driver.save_screenshot('img.png')
    elements = driver.find_elements(By.CLASS_NAME, 'ais-InfiniteHits-item')
    print(f'Found {len(elements)} courses')
    courses = []
    for i, element in enumerate(elements):
        element.screenshot(f'img{i}.png')
        # print(i)
        try:
            link = element.find_element(By.TAG_NAME, 'a').get_attribute('href')
            title = element.find_element(By.CLASS_NAME, 'card-title').text
            difficulty = element.find_element(By.CLASS_NAME, 'difficulty').text
            author = element.find_element(By.CLASS_NAME, 'partner-name').text
            rate = element.find_element(By.CLASS_NAME, 'ratings-text').text

            courses.append({
                'title': title,
                'difficulty': difficulty,
                'rate': rate,
                'author': author,
                'link': link,
            })
        except Exception as e:
            # print(e)
            pass
    data = pd.DataFrame(courses)
    return data

def find_netology_courses(query, level=1):
    level = {0: 'neo', 1: 'neo', 2: 'pro', 3: 'pro'}[level]

    url = "https://netology.ru/backend/api/search/programs"
    response = requests.get(url, params=[('term', query)]).json()['programs']
    courses = list(filter(lambda x: x['educational_level'] is not None and x['educational_level']['slug'] == level, response))
    return pd.DataFrame(courses)

def get_courses(data, user):
    actual_vacancy = get_actual_vacancy(data, user)
    update_skills = user['skills']
    vacancy_skills = []

    for skills in actual_vacancy.key_skills:
        for skill in skills:
            vacancy_skills.append(skill)
            if skill not in update_skills:
                update_skills[skill.upper()] = 0
    vacancy_skills = set(vacancy_skills)
    print(vacancy_skills)
    print(len(update_skills), update_skills)
    update_skills = {skill: level for skill, level in update_skills.items() if level != 0 or skill in vacancy_skills}
    
    courses = {}
    print(len(update_skills), update_skills)
    for skill, level in update_skills.items():
        courses1 = find_coursera_courses(driver, skill, level=level).iloc[:3]
        if len(courses1):
            courses1 = courses1[['title', 'author', 'link']]
            print(courses1)
            # courses2 = find_netology_courses(skill, level=level)
            # courses2 = courses2[['name', 'url']].rename(columns={'name': 'title', 'url': 'link'}).iloc[:2]
            # courses2.author = pd.Series(['Нетология'] * len(courses2))
            courses[skill] = json.loads(courses1.to_json())# .append(courses2)
    return courses, json.loads(actual_vacancy.to_json())