import webview
from constants import Constants
from server import app

if __name__ == '__main__':
    consts = Constants()
    webview.create_window(f'{consts.project_name} | {consts.title}', 'http://127.0.0.1:8080', fullscreen=False)
    webview.start()
