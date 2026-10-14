import os,sys,pathlib
stage=pathlib.Path(__file__).resolve().parent
os.chdir(stage)
sys.path.insert(0,str(stage))
import dotenv
dotenv.load_dotenv=lambda *a,**k: False
import requests
def demo_network_disabled(*a,**k):
 raise requests.exceptions.RequestException('External analysis is disabled for synthetic demo domains')
requests.sessions.Session.request=demo_network_disabled
import crawler_app
crawler_app.app.run(host='127.0.0.1',port=5057,debug=False,use_reloader=False)
