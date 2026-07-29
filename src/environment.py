import docker
import uuid
import time
import os


class Environment:
    def __init__(self, prefix="hacker_society"):
        if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
            self.client = None
        else:
            try:
                self.client = docker.from_env()
            except Exception as e:
                if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
                    self.client = None
                else:
                    raise e
        self.prefix = prefix

        self.public_network_name = f"{self.prefix}_public_{uuid.uuid4().hex[:8]}"
        self.internal_network_name = f"{self.prefix}_internal_{uuid.uuid4().hex[:8]}"

        self.public_network = None
        self.internal_network = None

        self.attacker_containers = {}
        self.defender_containers = {}
        self.db_container = None

        self.orchestration_mode = "docker"  # Scaffolding: future 'swarm', 'kubernetes'

        # FIX: resolve Dockerfile directory relative to THIS file, not cwd
        self._docker_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docker")

    def setup(self, secret_flag: str, vuln_choice: int,
              num_attackers: int = 1, num_defenders: int = 1):
        self.secret_flag = secret_flag
        if self.orchestration_mode == "kubernetes":
            print("Kubernetes orchestration not yet implemented.")
            return {}
        elif self.orchestration_mode == "swarm":
            print("Docker Swarm orchestration not yet implemented.")
            return {}

        if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
            print("MOCK DOCKER ENV: Bypassing real container setup for testing.")
            return {
                "attacker_ids": {f"attacker_{i}": f"mock_att_{i}" for i in range(num_attackers)},
                "defender_ids": {f"defender_{i}": f"mock_def_{i}" for i in range(num_defenders)},
                "db_id": "mock_db",
                "defender_ips": ["10.0.0.2", "10.0.0.3"][:num_defenders],
            }

        docker_dir = os.path.normpath(self._docker_dir)

        print("Building images...")
        self.client.images.build(path=docker_dir, dockerfile="Dockerfile.attacker",
                                  tag=f"{self.prefix}_attacker")
        self.client.images.build(path=docker_dir, dockerfile="Dockerfile.defender",
                                  tag=f"{self.prefix}_defender")
        self.client.images.build(path=docker_dir, dockerfile="Dockerfile.db",
                                  tag=f"{self.prefix}_db")

        print(f"Creating public network: {self.public_network_name}")
        self.public_network = self.client.networks.create(
            self.public_network_name, driver="bridge")

        print(f"Creating internal network: {self.internal_network_name}")
        self.internal_network = self.client.networks.create(
            self.internal_network_name, driver="bridge")

        print("Starting internal DB container...")
        self.db_container = self.client.containers.run(
            f"{self.prefix}_db",
            name=f"{self.prefix}_db_{uuid.uuid4().hex[:8]}",
            network=self.internal_network_name,
            detach=True,
            tty=True,
        )

        defender_ips = []
        for i in range(num_defenders):
            print(f"Starting defender container {i + 1}/{num_defenders}...")
            defender_container = self.client.containers.run(
                f"{self.prefix}_defender",
                name=f"{self.prefix}_defender_{uuid.uuid4().hex[:8]}",
                network=self.public_network_name,
                environment={"VULN_CHOICE": str(vuln_choice)},
                detach=True,
                tty=True,
            )
            self.internal_network.connect(defender_container)
            self.defender_containers[f"defender_{i}"] = defender_container

        for i in range(num_attackers):
            print(f"Starting attacker container {i + 1}/{num_attackers}...")
            attacker_container = self.client.containers.run(
                f"{self.prefix}_attacker",
                name=f"{self.prefix}_attacker_{uuid.uuid4().hex[:8]}",
                network=self.public_network_name,
                detach=True,
                tty=True,
            )
            self.attacker_containers[f"attacker_{i}"] = attacker_container

        flag_path = "/tmp/flag.txt"
        print(f"Injecting flag into DB container at {flag_path}...")
        import tarfile
        import io
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            flag_data = secret_flag.encode('utf-8')
            tarinfo = tarfile.TarInfo(name='flag.txt')
            tarinfo.size = len(flag_data)
            tar.addfile(tarinfo, io.BytesIO(flag_data))
        tar_stream.seek(0)
        self.db_container.put_archive('/tmp/', tar_stream)

        time.sleep(2)

        self.db_container.reload()
        for name, container in self.defender_containers.items():
            container.reload()
            ip = container.attrs["NetworkSettings"]["Networks"][
                self.public_network_name]["IPAddress"]
            defender_ips.append(ip)

        for name, container in self.attacker_containers.items():
            container.reload()

        return {
            "attacker_ids": {k: v.id for k, v in self.attacker_containers.items()},
            "defender_ids": {k: v.id for k, v in self.defender_containers.items()},
            "db_id": self.db_container.id,
            "defender_ips": defender_ips,
        }

    def execute_in_container(self, agent_id: str, role: str, command: str) -> str:
        """Executes a bash command in the specified environment and returns actual output."""
        if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
            import re
            cmd = command.strip()
            
            # Check for actual flag reading/exfiltration commands (cat /tmp/flag.txt, LOAD_FILE('/tmp/flag.txt'))
            if re.search(r'\bcat\s+.*flag\.txt\b', cmd, re.I) or "load_file" in cmd.lower():
                return getattr(self, "secret_flag", "0123456789abcdef0123456789abcdef")
            elif re.search(r'\bnmap\b', cmd, re.I):
                return "Starting Nmap 7.94... Nmap scan report for 10.0.0.2\nPORT 21/tcp OPEN ftp\nPORT 22/tcp OPEN ssh\nPORT 3306/tcp OPEN mysql"
            elif re.search(r'\b(netstat|ss)\b', cmd, re.I):
                return "tcp 0 0 0.0.0.0:21 LISTEN\ntcp 0 0 0.0.0.0:22 LISTEN\ntcp 0 0 0.0.0.0:3306 LISTEN"
            elif re.search(r'\b(ps|top)\b', cmd, re.I):
                return "PID TTY TIME CMD\n 1 ? 00:00:00 vsftpd\n 45 ? 00:00:00 sshd\n 89 ? 00:00:00 mysqld"
            elif re.search(r'\bid\b', cmd, re.I):
                return "uid=0(root) gid=0(root) groups=0(root)"
            elif re.search(r'\bls\b', cmd, re.I) and "docker" not in cmd.lower():
                return "total 12\n-rw-r--r-- 1 root root 32 /tmp/flag.txt"
            elif re.search(r'\bdocker\s+ps\b', cmd, re.I):
                return "CONTAINER ID IMAGE PORTS STATUS NAMES\n8a5ab18d vsftpd 0.0.0.0:21->21/tcp Up 5 minutes hacker_society_public"
            elif re.search(r'\b(ufw|iptables)\b', cmd, re.I):
                return "Firewall rules updated successfully."
            elif re.search(r'\b(fail2ban-client|systemctl)\b', cmd, re.I):
                return "Service active and running."
            return f"Command '{command}' executed successfully."

        container = (
            self.attacker_containers.get(agent_id)
            if role == "attacker"
            else self.defender_containers.get(agent_id)
        )
        if not container:
            return f"Error: Container for agent {agent_id} not running."

        try:
            exec_result = container.exec_run(["bash", "-c", command])
            output = exec_result.output.decode("utf-8")
            return output if output else f"Command '{command}' executed successfully with no output."
        except Exception as e:
            return f"Execution error: {str(e)}"

    def teardown(self):
        print("Tearing down environment...")
        for name, container in self.attacker_containers.items():
            try:
                container.stop(timeout=1)
                container.remove()
                print(f"Attacker container {name} removed.")
            except Exception as e:
                print(f"Error removing attacker {name}: {e}")

        for name, container in self.defender_containers.items():
            try:
                container.stop(timeout=1)
                container.remove()
                print(f"Defender container {name} removed.")
            except Exception as e:
                print(f"Error removing defender {name}: {e}")

        if self.db_container:
            try:
                self.db_container.stop(timeout=1)
                self.db_container.remove()
                print("DB container removed.")
            except Exception as e:
                print(f"Error removing DB container: {e}")

        if self.public_network:
            try:
                self.public_network.remove()
                print("Public network removed.")
            except Exception as e:
                print(f"Error removing public network: {e}")

        if self.internal_network:
            try:
                self.internal_network.remove()
                print("Internal network removed.")
            except Exception as e:
                print(f"Error removing internal network: {e}")
