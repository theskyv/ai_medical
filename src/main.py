#先cd到/src目录下 在终端执行python main.py app

from argparse import  ArgumentParser

if __name__ == '__main__':
    arg_parse = ArgumentParser(usage='usage:main.py action')
    arg_parse.add_argument('action',choices=['app'])

    args = arg_parse.parse_args()
    action = args.action

    match action:
        case 'app':
         from web.app import web_serve
         web_serve()
