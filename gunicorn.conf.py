# Gunicorn configuration
# Timeout extendido para soportar transcripciones largas con AssemblyAI
timeout = 300          # 5 minutos (AssemblyAI puede tardar en audios largos)
workers = 2
worker_class = "sync"
bind = "0.0.0.0:10000"
