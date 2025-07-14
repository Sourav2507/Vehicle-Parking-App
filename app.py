from flask import Flask



def createApp():
    app = Flask(__name__)
    return app

app = createApp()

@app.route("/")
def home():
    return "Hello Flask"

if (__name__ == '__main__'):
    app.run(debug=True,port=7000)