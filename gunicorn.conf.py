# Gunicorn configuration
# Timeout extendido para soportar transcripciones largas con Groq Whisper
timeout = 300          # 5 minutos (audios largos pueden tardar)
workers = 2
worker_class = "sync"
bind = "0.0.0.0:10000"
