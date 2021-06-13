from app import app
from scripts import get_vacancies, connect, get_courses

import os
import json
from threading import Thread
from uuid import uuid4 as uuid
import pandas as pd
from flask import request, jsonify
import requests

from tensorflow.keras.preprocessing.text import Tokenizer
from scipy.spatial.distance import cosine


@app.route('/first-step', methods=['post'])
def first_step_action():
    id = str(uuid())
    name = request.form.get('name')
    profession = request.form.get('profession')
    
    def load_vacancies(id, profession):
        db, cursor = connect()
        query = "SELECT * FROM queries WHERE profession=%s AND DATEDIFF(NOW(), created_at) <= 7"
        cursor.execute(query, (profession,))
        data = cursor.fetchone()
        print('data', data)
        if data:
            filename = data['_vacancy_table']
        else:
            print('get_vacancies')
            vacancies = get_vacancies(profession.strip())
            filename = os.path.join('cached', id + '.json')
            vacancies.to_json(filename)
        query = "UPDATE queries SET _vacancy_table=%s WHERE uuid=%s"
        print(filename) 
        cursor.execute(query, (filename, id))
        db.commit()
        db.close()

    thread = Thread(target=load_vacancies, args=(id, profession))
    thread.daemon = True
    thread.start()

    db, cursor = connect()
    query = "INSERT INTO queries (uuid, name, profession, created_at) VALUES (%s, %s, %s, NOW())"
    cursor.execute(query, (id, name, profession))
    db.commit()
    return jsonify({'query_id': id})

@app.route('/second-step/ready/<string:id>', methods=['get'])
def check_status(id):
    db, cursor = connect()
    query = "SELECT * FROM queries WHERE uuid=%s"
    cursor.execute(query, (id,))
    data = cursor.fetchone()
    db.close()
    if data is None:
        return jsonify({'status': 'NOT READY'})
    else:
        if data['_vacancy_table'] is not None:
            def get_top_skills(vacancy_data):
                skills = vacancy_data['key_skills'].copy()

                tokenizer = Tokenizer(num_words=400)
                tokenizer.fit_on_texts(skills)

                top_skills = list(tokenizer.index_word.values())[:5]

                return top_skills, list(tokenizer.index_word.values())

            data = pd.read_json(data['_vacancy_table'])
            print(data.head(5))
            top_skills, skills = get_top_skills(data)
            return jsonify({'status': 'OK', 'top_skills': top_skills, 'skills': skills})
        else:
            return jsonify({'status': 'NOT READY'})

@app.route('/third-step/<string:id>', methods=['put'])
def third_step(id):
    user = json.loads(request.data)
    print(user)
    if 'skills' not in user:
        return "", 404

    db, cursor = connect()
    query = "SELECT * FROM queries WHERE uuid=%s"
    cursor.execute(query, (id,))
    data = cursor.fetchone()
    db.close()
    data = pd.read_json(data['_vacancy_table'])
    courses, vacancies = get_courses(data, user)
    print(courses)
    courses = {
        skill: [
            {
                'title': list(courses[skill]['title'].values())[i], 
                'link': list(courses[skill]['link'].values())[i] 
            }
            for i in range(len(courses[skill]['title']))] for skill in courses
    }
    vacancies = [
        {
            'name': list(vacancies['name'].values())[i], 
            'salary': list(vacancies['salary'].values())[i], 
            'key_skills': list(vacancies['key_skills'].values())[i],
        } 
        for i in range(len(vacancies['name']))
    ]
    return jsonify({'courses': courses, 'skills': list(courses.keys()), 'vacancies': vacancies})