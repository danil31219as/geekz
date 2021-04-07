import pandas as pd
import numpy as np

lessons = pd.read_excel('lessons1.xlsx')


def get_column(column, i):
  if column == 'lesson':
    return [f"lesson{i + 1}_visit", f"lesson{i + 1}_progress"]
  if column == 'lessonWebinar':
    return [f"lessonWebinar{i + 1}_visit", '']
  if column == 'lessonTest':
    return [f"lessonTest{i + 1}_score", '']
  
  
lesson_columns = [elem for i in range(len(lessons[lessons.id_groups == 60259])) for elem in get_column(lessons['type'][i], i) if elem]
df = pd.DataFrame(np.arange(1, 301).reshape(300, 1), columns=['user_id'])
for column in lesson_columns:
  if 'score' in column:
    df[column] = np.random.randint(0, 100, (300))
  if 'visit' in column:
    df[column] = np.random.choice([0, 1], (300))
  if 'progress' in column:
    df[column] = np.random.randint(0, 100, (300))
df.to_csv('users.csv', index=False, encoding='utf-16')
