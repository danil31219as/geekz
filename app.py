import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)


def data_for_visit(table_name):
    x, y = [], []
    visit_list = [(data, index.split("_")[0]) for index, data in
                  pd.read_csv(f"{table_name}", sep=",").mean().iteritems() if
                  "visit" in index]
    for i in visit_list:
        x.append(i[1])
        y.append(i[0])
    return x, y


def data_for_progress(table_name):
    x, y = [], []
    progress_list = [(data, index.split("_")[0]) for index, data in
                     pd.read_csv(f"{table_name}", sep=",").median().iteritems()
                     if
                     "progress" in index]
    for i in progress_list:
        x.append(i[1])
        y.append(i[0])
    return x, y


def average_test(table_name):
    x, y = [], []
    df = pd.read_csv(f"{table_name}", sep=",")
    x = list(df["user_id"])
    for index, data in df.iteritems():
        if "Test" not in index:
            df = df.drop([index], axis=1)
    df = df.mean(axis=1)
    for index, data in df.iteritems():
        y.append(data)
    return x, y


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
    y = list(10 * mark / mark_count * visit / visit_count / (last + 10))
    return x, y


df = pd.read_csv(f"data.csv", sep=",")


def conversion_rate(df, first_course, second_course):
    return (len(df.query(
        f"course == {first_course} | course == {second_course}")) - len(
        set(df.query(f"course == {first_course} | course == {second_course}")[
                "user_id"]))) / len(
        df.query(f"course == {first_course}")) * 100


d = {}
for i in range(1, 4):
    d[i] = {}
    for j in range(1, 4):
        d[i][j] = conversion_rate(df, i, j)


@app.route('/')
def index():
    params = {1: [1, 10, 100], 2: [100, 1, 10]}
    sum_counts = [27.92, 17.53, 14.94, 26.62, 12.99]
    colors = ["#FF0000", "#00e676", "#ff5722", "#1e88e5", "#ffd600"]
    return render_template('index.html', data=params, colors=colors)


if __name__ == '__main__':
    app.run()
