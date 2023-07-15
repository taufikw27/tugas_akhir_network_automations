from flask import Flask
import paramiko


command = "qm set 111 --memory 256"
app = Flask(__name__)

host = "10.0.0.93"
username = "root"
password = "tkj18"

@app.route("/")
def hello():
	client = paramiko.client.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(host, username=username, password=password)
	_stdin, _stdout,_stderr = client.exec_command("qm set 111 --memory 256")
	# client.close()
	return _stdout.read().decode()
	# print(_out.read().decode()

if __name__ == '__main__':
	app.run()