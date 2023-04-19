import webview
from constants import Constants
from server import app

if __name__ == '__main__':
    consts = Constants()
    webview.create_window(f'{consts.project_name} | {consts.title}', app, fullscreen=False)
    webview.start(debug=True)