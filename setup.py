[loggers]
keys=root

[handlers]
keys=jsonHandler

[formatters]
keys=jsonFormatter

[logger_root]
level=INFO
handlers=jsonHandler

[handler_jsonHandler]
class=logging.StreamHandler
level=INFO
formatter=jsonFormatter
args=(sys.stdout,)

[formatter_jsonFormatter]
class=pythonjsonlogger.jsonlogger.JsonFormatter
format=%(asctime)s %(name)s %(process)d %(thread)d %(levelname)s %(message)s