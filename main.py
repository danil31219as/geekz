from flask import Flask, render_template  # this has changed

app = Flask(__name__)


@app.route('/')
def index():
    sum_counts = [27.92, 17.53, 14.94, 26.62, 12.99]
    colors = ["#FF0000", "#00e676", "#ff5722", "#1e88e5", "#ffd600"]
    return render_template('main.html', data=sum_counts, colors=colors)


if __name__ == '__main__':
    app.run()
