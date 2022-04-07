""" To start the web server """
from conferenceapp2 import app
if __name__=='__main__':
    app.run(debug=True,port=5050)