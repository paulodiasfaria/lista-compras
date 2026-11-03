"""
WSGI config para PythonAnywhere.

O plano gratuito so permite 1 dominio/1 web app. Este app vive ao lado do
eventos-app no MESMO dominio, montado em /compras via DispatcherMiddleware.

No separador "Web" da PythonAnywhere, no "WSGI configuration file", usa algo
como isto (ajusta os caminhos conforme a tua conta):
"""
import sys
import os
import importlib.util
from werkzeug.middleware.dispatcher import DispatcherMiddleware

compras_home = '/home/paulodiasfaria/lista-compras'
eventos_home = '/home/paulodiasfaria/eventos-app'
jobs_home = '/home/paulodiasfaria/job-search'

os.environ['COMPRAS_DB_PATH'] = '/home/paulodiasfaria/lista-compras/compras.db'
os.environ['COMPRAS_API_KEY'] = 'DEFINE-UMA-CHAVE-SECRETA-AQUI'
os.environ['COMPRAS_UPLOAD_DIR'] = '/home/paulodiasfaria/lista-compras/uploads'
os.environ['EVENTOS_DB_PATH'] = '/home/paulodiasfaria/eventos-app/eventos.db'
os.environ['EVENTOS_API_KEY'] = 'DEFINE-OUTRA-CHAVE-SECRETA-AQUI'
os.environ['JOBS_DB_PATH'] = '/home/paulodiasfaria/job-search/jobs.db'
os.environ['JOBS_API_KEY'] = 'DEFINE-UMA-TERCEIRA-CHAVE-SECRETA-AQUI'
os.environ['JOBS_UPLOAD_DIR'] = '/home/paulodiasfaria/job-search/uploads'


def load_app_module(name, project_dir):
    """Carrega app.py de uma pasta com um nome de modulo unico, para nao
    colidir no sys.modules (ambos os projetos tem um ficheiro 'app.py')."""
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    spec = importlib.util.spec_from_file_location(name, os.path.join(project_dir, "app.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


eventos_module = load_app_module("eventos_app_module", eventos_home)
compras_module = load_app_module("compras_app_module", compras_home)
jobs_module = load_app_module("jobs_app_module", jobs_home)

application = DispatcherMiddleware(eventos_module.app, {
    '/compras': compras_module.app,
    '/jobs': jobs_module.app,
})
