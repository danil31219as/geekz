import os
import pickle
import catboost
import numpy as np
import pandas as pd
from flask import Flask, render_template, send_from_directory, request

application = Flask(__name__)
black_list = ['гибддмвдроссии', 'банкомат']
# df_store = pd.read_csv('df_store.csv')
# store_matrix = np.array(df_store)[:, 1:]
# store_names = df_store['name']
# check_model = catboost.CatBoostClassifier().load_model('check_model.pkl')
# big_model = catboost.CatBoostClassifier().load_model('big_model.pkl')
# small_model = catboost.CatBoostClassifier().load_model('small_model.pkl')
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)
users_df = pd.read_csv('data/users.csv', encoding='utf-16')

def make_predict(users_df):
    mean_df = pd.DataFrame({'user_id': users_df['user_id']})

    mean_df['score'] = np.zeros(len(users_df))
    mean_df['visit'] = np.zeros(len(users_df))
    mean_df['progress'] = np.zeros(len(users_df))

    count_score = 0
    count_visit = 0
    count_progress = 0
    for column in users_df.columns:
        if 'score' in column:
            mean_df['score'] += users_df[column]
            count_score += 1
        elif 'visit' in column:
            mean_df['visit'] += users_df[column]
            count_visit += 1
        elif 'progress' in column:
            mean_df['progress'] += users_df[column]
            count_progress += 1
    mean_df['score'] /= count_score * 100
    mean_df['visit'] /= count_visit
    mean_df['progress'] /= count_progress * 100
    mean_df.pop('user_id')

    y_hc = model.predict(mean_df)
    mean_df['user_id'] = users_df['user_id']
    return y_hc, mean_df


def data_for_visit(table_name):
    x, y = [], []
    table = pd.read_csv(f"{table_name}", sep=",")
    visit_list = [(data * 100, index.split("_")[0]) for index, data in
                  table.mean().iteritems() if
                  "visit" in index]
    visits = np.array([np.array(table[column]) for column in table.columns if
                       'visit' in column])

    for i in visit_list:
        x.append(i[1].replace('lesson', 'Урок'))
        y.append(i[0])
    return {0: x, 1: y, 100: str(
        round(visits.sum() * 100 / visits.shape[0] / visits.shape[1],
              2)) + ' - метрика'}


def data_for_progress(table_name):
    x, y = [], []
    progress_list = [(data, index.split("_")[0]) for index, data in
                     pd.read_csv(f"{table_name}", sep=",").median().iteritems()
                     if
                     "progress" in index]
    for i in progress_list:
        x.append(i[1].replace('lesson', 'Урок'))
        y.append(i[0])
    return {0: x, 1: y}


def average_test(table_name):
    x, y = [], []
    df = pd.read_csv(f"{table_name}", sep=",")
    x = list(df["user_id"])
    for index, data in df.iteritems():
        if "Test" not in index:
            df = df.drop([index], axis=1)
    df = df.mean(axis=1)
    for index, data in df.iteritems():
        y.append(round(data, 2))
    return {0: x, 1: y}


def retention(table_name):
    df = pd.read_csv(f"{table_name}", sep=",")
    x = list(df["user_id"])
    last = df['last']
    mark = np.zeros(len(df))
    visit = np.zeros(len(df))
    mark_count = 0
    visit_count = 0
    for index, data in df.iteritems():
        if "progress" in index:
            mark += data
            mark_count += 1
        if "visit" in index:
            visit += data
            visit_count += 1
    y = list(
        np.round(10 * mark / mark_count * visit / visit_count / (last + 10), 2))
    return {0: x[:30], 1: y[:30],
            100: str(np.array(y).mean().round(2)) + ' - средняя метрика'}


df = pd.read_csv(f"data/data.csv", sep=",")


def conversion_rate(df, first_course, second_course):
    return np.round((len(df.query(
        f"course == {first_course} | course == {second_course}")) - len(
        set(df.query(f"course == {first_course} | course == {second_course}")[
                "user_id"]))) / len(
        df.query(f"course == {first_course}")) * 100, 2)


d = {}
for i in range(1, 4):
    d[i] = {}
    for j in range(1, 4):
        d[i][j] = conversion_rate(df, i, j)

tables = os.listdir('data/groups')
group_course = {'course_1_low.csv':'1 курс - низкая группа', 'course_1_middle.csv':'1 курс - средняя группа',
                'course_1_mix.csv':'1 курс - смешанная группа', 'course_1_top.csv':'1 курс - высокая группа',
                "course_2_low.csv":'2 курс - низкая группа', "course_2_middle.csv":'2 курс - средняя группа',
                "course_2_mix.csv":'2 курс - смешанная группа', "course_2_top.csv":'2 курс - высокая группа',
                "course_3_low.csv":'3 курс - низкая группа', "course_3_middle.csv":'3 курс - средняя группа',
                "course_3_mix.csv":'3 курс - смешанная группа', "course_3_top.csv":'3 курс - высокая группа'}


@application.route('/', methods=['GET', 'POST'])
def index():
    answer = ''
    if request.method == 'POST':
        key, val = list(request.files.items())[0]

        val.save('data/tables/' + val.filename)
        try:
            df = pd.read_csv('data/tables/' + val.filename)
            y_pred, res_df = make_predict(df)
            d_answers = {0: 'высокий', 2: 'средний', 1: 'низкий'}
            answer = f'Ученик с id {res_df.iloc[0, 3]} имеет {d_answers[y_pred[0]]} уровень'
            os.remove('data/tables/' + val.filename)
        except:
            os.remove('data/tables/' + val.filename)
            answer = 'Неверный формат файла'


    d_progress = {}
    d_visit = {}
    d_retention = retention('data/users_last.csv')
    d_test = average_test('data/users_last.csv')
    groups = []
    for i in range(12):
        groups.append(group_course[tables[i]])
        d_progress[i] = data_for_progress('data/groups/' + tables[i])
        d_visit[i] = data_for_visit('data/groups/' + tables[i])

    d_progress[100] = [str(np.array(d_progress[i][1]).mean()) + ' - метрика' for
                       i in d_progress]
    table_conv = pd.read_csv('data/data.csv')
    d_conv = {i: {} for i in range(1, 4)}
    for i in range(1, 4):
        for j in range(1, 4):
            d_conv[i][j] = conversion_rate(table_conv, i, j)
    y_hc, mean_df = make_predict(users_df)
    top_score = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                 zip(mean_df.iloc[y_hc == 0, 3], mean_df.iloc[y_hc == 0, 0])]
    middle_score = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                    zip(mean_df.iloc[y_hc == 2, 3], mean_df.iloc[y_hc == 2, 0])]
    low_score = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                 zip(mean_df.iloc[y_hc == 1, 3], mean_df.iloc[y_hc == 1, 0])]

    top_visit = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                 zip(mean_df.iloc[y_hc == 0, 3], mean_df.iloc[y_hc == 0, 1])]
    middle_visit = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                    zip(mean_df.iloc[y_hc == 2, 3], mean_df.iloc[y_hc == 2, 1])]
    low_visit = [{'x': x, 'y': round(y * 100, 3)} for x, y in
                 zip(mean_df.iloc[y_hc == 1, 3], mean_df.iloc[y_hc == 1, 1])]
    return render_template('index.html', d_progress=d_progress,
                           group_course=groups, d_visit=d_visit,
                           d_retention=d_retention, d_test=d_test[1][:30],
                           d_conv=d_conv, top_score=top_score,
                           middle_score=middle_score, low_score=low_score,
                           top_visit=top_visit, middle_visit=middle_visit,
                           low_visit=low_visit, answer=answer, categories=['test'])


@application.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    directory = 'data/'
    return send_from_directory(directory=directory, filename=filename)

def predict(X, check_model, big_model, small_model):
    y_pred = []
    for obj in X:
        category = check_model.predict(obj)
        if category == 1:
            pred = big_model.predict(obj)
        else:
            pred = small_model.predict(obj)
        y_pred.append(pred[0])
    return np.array(y_pred)


categories = ['Pet',
              'Other',
              'Maintenance and building',
              'Design, print',
              'Tourism',
              'Railway and sea transport',
              'Local and autotransport',
              'Medical',
              'Taxi',
              'Postal services, delivery',
              'Active rest',
              'Auto',
              'Soft',
              'Providers',
              'Money',
              'Payments',
              'Clothes',
              'Cultural life',
              'Furniture, home',
              'Discount',
              'Supermarkets',
              'Parking&Fuel',
              'Kids',
              'Sport',
              'Services',
              'Restaurants',
              'Fast Food',
              'Digital goods',
              'Alcohol and tobacco',
              'Gift, hobby',
              'Legal and insurance',
              'Beauty',
              'Video games',
              'Gambling',
              'Education']
translate_category = {'Pet': 'Домашние животные', 'Other': 'Другое',
                      'Maintenance and building': 'Техническое обслуживание и строительство',
                      'Design, print': 'Дизайн, печать', 'Tourism': 'Туризм',
                      'Railway and sea transport': 'Железнодорожный и морской транспорт',
                      'Local and autotransport': 'Автотранспорт',
                      'Medical': 'Медицинские', 'Taxi': 'Такси',
                      'Postal services, delivery': 'Почтовые услуги, доставка',
                      'Active rest': 'Активный отдых', 'Auto': 'Авто',
                      'Soft': 'Безалкогольная продукция',
                      'Providers': 'Услуги поставщиков', 'Money': 'Деньги',
                      'Payments': 'Платежи',
                      'Clothes': 'Одежда', 'Cultural life': 'Культурная жизнь',
                      'Furniture, home': 'Мебель, для дома',
                      'Discount': 'Дискаунт',
                      'Supermarkets': 'Супермаркеты',
                      'Parking&Fuel': 'Парковки И Топливо',
                      'Kids': 'Дети', 'Sport': 'Спорт', 'Services': 'Услуги',
                      'Restaurants': 'Рестораны', 'Fast Food': 'Фастфуд',
                      'Digital goods': 'Цифровые товары',
                      'Alcohol and tobacco': 'Алкоголь и табак',
                      'Gift, hobby': 'Подарок, хобби',
                      'Legal and insurance': 'Юрисдикция и страхование',
                      'Beauty': 'Красота',
                      'Video games': 'Видео-игры', 'Gambling': 'Азартные игры',
                      'Education': 'Образование'}


@application.route('/business-ecosystem', methods=['post', 'get'])
def main():
    params = {'categories': categories, 'translate': translate_category,
              'is_rate': False, 'is_effect': False}
    if request.method == 'POST':
        if request.form.get('rate'):
            name = request.form.get('name')
            age = float(request.form.get('age'))
            male = float(request.form.get('male'))
            female = float(request.form.get('female'))
            married = float(request.form.get('married'))
            count = float(request.form.get('count'))
            if male >= 1:
                male /= count
            if female >= 1:
                female /= count
            if married >= 1:
                married /= count
            current_categories = np.zeros(len(categories))
            for i in request.form.getlist('category'):
                current_categories[int(i) - 1] = 1
            data = np.array([np.concatenate((np.array(
                [abs(age - store_matrix[j, 0]),
                 male / store_matrix[j, 1],
                 female / store_matrix[j, 2],
                 married / store_matrix[j, 3],
                 store_matrix[j, 4] / count]),
                                             current_categories + store_matrix[
                                                                  j, 5:])) for j
                in range(len(store_names))])
            rate = 0
            rating = []
            for elem in sorted(
                    zip(predict(data, check_model, big_model, small_model),
                        store_names), key=lambda x: -x[0]):
                if elem[1] not in black_list:
                    rating.append([elem[1].capitalize(), round(elem[0], 2)])
                    rate += 1
                if rate == 10:
                    break

            params['is_rate'] = True
            params['rating'] = rating
            params['name'] = name
    return render_template('ecosystem.html', **params)

if __name__ == '__main__':
    application.run(host='0.0.0.0')
