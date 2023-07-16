from audioop import mul
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import paramiko
import mysql.connector
import os

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="netau")
mycursor = mydb.cursor()


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Konfigurasi sesi Flask
app.config['SESSION_TYPE'] = 'filesystem'

def check_server_status(ip_add, username, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=ip_add, username=username, password=password)
        ssh.close()
        return True
    except:
        return False
@app.route("/", methods=['GET', 'POST'])
def index():
    global ip_add, cookie, node_name, username, password
    if request.method == 'GET':
        return render_template('vertical/pages-login.html')

    if request.method == 'POST':
        ip_add = request.form['ip_address']
        username = request.form['username']
        password = request.form['password']
        session['username'] = username
        session['password'] = password
        session['ipadd'] = ip_add
        
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        mycursor.execute(query, (username, password))
        # Periksa hasil query
        if mycursor.fetchone():
            flash("Username dan password valid")
        else:
            flash('Username atau password salah', 'error')
            return render_template('vertical/pages-login.html')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if check_server_status(ip_add, username, password):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip_add, username=username, password=password)
            cmd = "service --status-all"
            # Jalankan perintah pada host target
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            daftar_layanan = output.split('\n')
            ssh.close()
            return render_template('vertical/index.html', username=username, service=daftar_layanan)
        else:
            flash('Server Masih Dalam Keadaan Mati', 'error')
            return render_template('vertical/pages-login.html')
    
    

@app.route("/dashboard", methods=['GET'])
def dashboard():
        username = session.get('username')
        password = session.get('password')
        ip_add = session.get('ipadd')
        # print(username)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=ip_add, username=username, password=password)
        cmd = "service --status-all"
        # Jalankan perintah pada host target
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        daftar_layanan = output.split('\n')
        ssh.close();
        return render_template('vertical/index.html',username=username, service=daftar_layanan)
@app.route("/form-install", methods=['GET', 'POST'])
def formInstall():
    username = session.get('username')
    password = session.get('password')
    ip_add = session.get('ipadd')
    if request.method == 'GET':
        query = "SELECT * FROM nodes"
        query2 = "SELECT * FROM services"
        mycursor.execute(query)
        servers = mycursor.fetchall()  # Fetch all rows returned by the query
        mycursor.execute(query2)
        services = mycursor.fetchall()  # Fetch all rows returned by the query
        return render_template('vertical/form-advanced.html', servers=servers, services=services)
    
    if request.method == 'POST':
        selected_servers = request.form.getlist('selected_servers[]')
        selected_services = request.form.getlist('selected_services[]')

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=ip_add, username=username, password=password)
            # command = "cd /home/muhtaufikw/"
            # stdin, stdout, stderr = ssh.exec_command(command)
            for server in selected_servers:
                for service in selected_services:
                    cmd = f"ansible-playbook -i inventory {service}-{server}.yml"
                    # cmd = "pwd"
                    # print(cmd)
                    # Jalankan perintah pada host target
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode()
                    errors = stderr.read().decode()
                    
                    if output:
                        flash("Service Berhasil di Install", "success")
                        print("Output:", output)
                    if errors:
                        flash("Terjadi kesalahan saat menjalankan perintah.", "error")
                        print("Errors:", errors)
        
        except paramiko.AuthenticationException:
            flash("Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            flash("SSH error: " + str(e))
        except paramiko.socket.error as e:
            flash("Socket error: " + str(e))
        except Exception as e:
            flash("Error: " + str(e))
        
        ssh.close()
        return redirect(url_for('dashboard'))
           

if __name__ == '__main__':
    app.run(debug=True)

