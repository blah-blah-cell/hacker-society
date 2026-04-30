import os
import subprocess
import time
import sys

def setup_vuln_1():
    # Anonymous FTP Server
    print("Setting up Vulnerability 1: Anonymous FTP Server")
    with open('/etc/vsftpd.conf', 'w') as f:
        f.write("listen=YES\nanonymous_enable=YES\nlocal_enable=YES\nwrite_enable=YES\nanon_upload_enable=YES\nanon_mkdir_write_enable=YES\n")
    os.system("mkdir -p /var/ftp/pub && chmod 777 /var/ftp/pub")
    subprocess.Popen(["vsftpd", "/etc/vsftpd.conf"])

def setup_vuln_2():
    # Weak SSH Credentials
    print("Setting up Vulnerability 2: Weak SSH Credentials")
    os.system("mkdir -p /var/run/sshd")
    os.system("echo 'root:toor' | chpasswd")
    with open('/etc/ssh/sshd_config', 'a') as f:
        f.write("\nPermitRootLogin yes\nPasswordAuthentication yes\n")
    subprocess.Popen(["/usr/sbin/sshd", "-D"])

def setup_vuln_3():
    # Open Redis Server
    print("Setting up Vulnerability 3: Open Redis Server")
    with open('/etc/redis/redis.conf', 'w') as f:
        f.write("bind 0.0.0.0\nprotected-mode no\n")
    subprocess.Popen(["redis-server", "/etc/redis/redis.conf"])

def setup_vuln_4():
    # Open Memcached
    print("Setting up Vulnerability 4: Open Memcached")
    subprocess.Popen(["memcached", "-u", "root", "-l", "0.0.0.0", "-p", "11211"])

def setup_vuln_5():
    # SMB Guest Access
    print("Setting up Vulnerability 5: SMB Guest Access")
    with open('/etc/samba/smb.conf', 'w') as f:
        f.write("[global]\nworkgroup = WORKGROUP\nmap to guest = Bad User\n\n[public]\npath = /\nbrowsable =yes\nwritable = yes\nguest ok = yes\nread only = no\n")
    subprocess.Popen(["smbd", "--foreground", "--no-process-group"])

def setup_vuln_6():
    # Unauthenticated VNC
    print("Setting up Vulnerability 6: Unauthenticated VNC")
    os.environ['USER'] = 'root'
    os.system("mkdir -p ~/.vnc && echo 'password' | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd")
    subprocess.Popen(["vncserver", ":1", "-geometry", "800x600", "-depth", "16", "-SecurityTypes", "None"])

def setup_vuln_7():
    # Cleartext Telnet
    print("Setting up Vulnerability 7: Cleartext Telnet")
    with open('/etc/xinetd.d/telnet', 'w') as f:
        f.write("service telnet\n{\n disable = no\n flags = REUSE\n socket_type = stream\n wait = no\n user = root\n server = /usr/sbin/in.telnetd\n log_on_failure += USERID\n}\n")
    os.system("echo 'root:toor' | chpasswd")
    subprocess.Popen(["xinetd", "-dontfork"])

def setup_vuln_8():
    # Misconfigured NFS
    print("Setting up Vulnerability 8: Misconfigured NFS")
    with open('/etc/exports', 'w') as f:
        f.write("/ *(rw,sync,no_root_squash,no_subtree_check)\n")
    os.system("exportfs -a")
    # NFS in Docker can be tricky, simulating service start
    subprocess.Popen(["rpcbind", "-f"])

def setup_vuln_9():
    # Exposed Rsync Daemon
    print("Setting up Vulnerability 9: Exposed Rsync Daemon")
    with open('/etc/rsyncd.conf', 'w') as f:
        f.write("[root]\npath = /\nread only = no\nlist = yes\nuid = root\ngid = root\n")
    subprocess.Popen(["rsync", "--daemon", "--no-detach"])

def setup_vuln_10():
    # Exposed Docker Socket
    print("Setting up Vulnerability 10: Exposed Docker Socket (Simulated via socat)")
    # Typically this would forward /var/run/docker.sock to tcp, here we just listen to simulate it
    subprocess.Popen(["socat", "TCP-LISTEN:2375,fork", "EXEC:'echo Docker socket simulated'"])

def setup_vuln_11():
    # Open Elasticsearch (Simulated via python HTTP server returning fake ES responses)
    print("Setting up Vulnerability 11: Open Elasticsearch (Simulated)")
    code = "import http.server, socketserver\nclass Handler(http.server.SimpleHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200)\n  self.end_headers()\n  self.wfile.write(b'{\"name\" : \"es-node\", \"cluster_name\" : \"elasticsearch\", \"version\" : {\"number\" : \"7.10.0\"}}')\nsocketserver.TCPServer(('', 9200), Handler).serve_forever()"
    with open('/app/sim_es.py', 'w') as f: f.write(code)
    subprocess.Popen(["python3", "/app/sim_es.py"])

def setup_vuln_12():
    # Misconfigured Proxy (Squid)
    print("Setting up Vulnerability 12: Misconfigured Proxy (Squid)")
    with open('/etc/squid/squid.conf', 'w') as f:
        f.write("http_port 3128\nhttp_access allow all\n")
    subprocess.Popen(["squid", "-N", "-d", "1"])

def setup_vuln_13():
    # Vulnerable Distcc
    print("Setting up Vulnerability 13: Vulnerable Distcc")
    subprocess.Popen(["distccd", "--daemon", "--no-detach", "--user", "root", "--allow", "0.0.0.0/0", "--port", "3632"])

def setup_vuln_14():
    # Apache CouchDB (Simulated)
    print("Setting up Vulnerability 14: Apache CouchDB (Simulated)")
    code = "import http.server, socketserver\nclass Handler(http.server.SimpleHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200)\n  self.end_headers()\n  self.wfile.write(b'{\"couchdb\":\"Welcome\",\"version\":\"3.1.1\"}')\nsocketserver.TCPServer(('', 5984), Handler).serve_forever()"
    with open('/app/sim_couch.py', 'w') as f: f.write(code)
    subprocess.Popen(["python3", "/app/sim_couch.py"])

def setup_vuln_15():
    # Open MongoDB (Simulated)
    print("Setting up Vulnerability 15: Open MongoDB (Simulated via TCP port 27017)")
    subprocess.Popen(["socat", "TCP-LISTEN:27017,fork", "EXEC:'echo MongoDB simulated'"])

def setup_vuln_16():
    # PostgreSQL/MySQL Default Creds (Simulated)
    print("Setting up Vulnerability 16: PostgreSQL/MySQL Default Creds (Simulated)")
    subprocess.Popen(["socat", "TCP-LISTEN:5432,fork", "EXEC:'echo PostgreSQL simulated'"])
    subprocess.Popen(["socat", "TCP-LISTEN:3306,fork", "EXEC:'echo MySQL simulated'"])

def setup_vuln_17():
    # SNMP Default Community
    print("Setting up Vulnerability 17: SNMP Default Community")
    with open('/etc/snmp/snmpd.conf', 'w') as f:
        f.write("rocommunity public\n")
    subprocess.Popen(["snmpd", "-f", "-Lsd"])

def setup_vuln_18():
    # Jenkins Script Console (Simulated)
    print("Setting up Vulnerability 18: Jenkins Script Console (Simulated)")
    code = "import http.server, socketserver\nclass Handler(http.server.SimpleHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200)\n  self.end_headers()\n  self.wfile.write(b'Jenkins Script Console (Simulated)')\nsocketserver.TCPServer(('', 8080), Handler).serve_forever()"
    with open('/app/sim_jenkins.py', 'w') as f: f.write(code)
    subprocess.Popen(["python3", "/app/sim_jenkins.py"])

def setup_vuln_19():
    # Apache Tomcat Manager (Simulated)
    print("Setting up Vulnerability 19: Apache Tomcat Manager (Simulated)")
    code = "import http.server, socketserver\nclass Handler(http.server.SimpleHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(401)\n  self.send_header('WWW-Authenticate', 'Basic realm=\"Tomcat Manager Application\"')\n  self.end_headers()\n  self.wfile.write(b'Tomcat Manager (Simulated) - default creds tomcat:tomcat')\nsocketserver.TCPServer(('', 8080), Handler).serve_forever()"
    with open('/app/sim_tomcat.py', 'w') as f: f.write(code)
    subprocess.Popen(["python3", "/app/sim_tomcat.py"])

def setup_vuln_20():
    # Exposed etcd/Consul (Simulated)
    print("Setting up Vulnerability 20: Exposed etcd/Consul (Simulated)")
    code = "import http.server, socketserver\nclass Handler(http.server.SimpleHTTPRequestHandler):\n def do_GET(self):\n  self.send_response(200)\n  self.end_headers()\n  self.wfile.write(b'{\"etcdserver\":\"3.4.13\",\"etcdcluster\":\"3.4.0\"}')\nsocketserver.TCPServer(('', 2379), Handler).serve_forever()"
    with open('/app/sim_etcd.py', 'w') as f: f.write(code)
    subprocess.Popen(["python3", "/app/sim_etcd.py"])

def setup_vuln_21():
    # Hard Mode
    print("Setting up Vulnerability 21: Hard Mode (Standard SSH, secure config)")
    os.system("mkdir -p /var/run/sshd")
    os.system("echo 'root:$(openssl rand -base64 32)' | chpasswd")
    with open('/etc/ssh/sshd_config', 'a') as f:
        f.write("\nPermitRootLogin no\nPasswordAuthentication no\n")
    subprocess.Popen(["/usr/sbin/sshd", "-D"])

def main():
    vuln_choice = os.environ.get("VULN_CHOICE", "1")

    try:
        vuln_num = int(vuln_choice)
    except ValueError:
        vuln_num = 1

    if vuln_num == 1: setup_vuln_1()
    elif vuln_num == 2: setup_vuln_2()
    elif vuln_num == 3: setup_vuln_3()
    elif vuln_num == 4: setup_vuln_4()
    elif vuln_num == 5: setup_vuln_5()
    elif vuln_num == 6: setup_vuln_6()
    elif vuln_num == 7: setup_vuln_7()
    elif vuln_num == 8: setup_vuln_8()
    elif vuln_num == 9: setup_vuln_9()
    elif vuln_num == 10: setup_vuln_10()
    elif vuln_num == 11: setup_vuln_11()
    elif vuln_num == 12: setup_vuln_12()
    elif vuln_num == 13: setup_vuln_13()
    elif vuln_num == 14: setup_vuln_14()
    elif vuln_num == 15: setup_vuln_15()
    elif vuln_num == 16: setup_vuln_16()
    elif vuln_num == 17: setup_vuln_17()
    elif vuln_num == 18: setup_vuln_18()
    elif vuln_num == 19: setup_vuln_19()
    elif vuln_num == 20: setup_vuln_20()
    elif vuln_num == 21: setup_vuln_21()
    else:
        print(f"Unknown vuln choice {vuln_num}, defaulting to 1")
        setup_vuln_1()

    # Keep container alive
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
