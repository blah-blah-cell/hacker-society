import docker
import uuid
import time

class Environment:
    def __init__(self, prefix="hacker_society"):
        self.client = docker.from_env()
        self.prefix = prefix

        # We will create two networks
        self.public_network_name = f"{self.prefix}_public_{uuid.uuid4().hex[:8]}"
        self.internal_network_name = f"{self.prefix}_internal_{uuid.uuid4().hex[:8]}"

        self.public_network = None
        self.internal_network = None

        self.attacker_containers = {}
        self.defender_containers = {}
        self.db_container = None

        self.orchestration_mode = "docker" # Scaffolding: Future options 'swarm', 'kubernetes'

    def setup(self, secret_flag: str, vuln_choice: int, num_attackers: int = 1, num_defenders: int = 1):
        # Scaffolding for distributed orchestration
        if self.orchestration_mode == "kubernetes":
            print("Kubernetes orchestration not yet implemented.")
            return {}
        elif self.orchestration_mode == "swarm":
            print("Docker Swarm orchestration not yet implemented.")
            return {}

        import os
        if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
            print("MOCK DOCKER ENV: Bypassing real container setup for testing.")
            return {
                "attacker_ids": {f"attacker_{i}": f"mock_att_{i}" for i in range(num_attackers)},
                "defender_ids": {f"defender_{i}": f"mock_def_{i}" for i in range(num_defenders)},
                "db_id": "mock_db",
                "defender_ips": ["10.0.0.2", "10.0.0.3"][:num_defenders]
            }

        print("Building images...")
        self.client.images.build(path="./docker", dockerfile="Dockerfile.attacker", tag=f"{self.prefix}_attacker")
        self.client.images.build(path="./docker", dockerfile="Dockerfile.defender", tag=f"{self.prefix}_defender")
        self.client.images.build(path="./docker", dockerfile="Dockerfile.db", tag=f"{self.prefix}_db")

        print(f"Creating public network: {self.public_network_name}")
        self.public_network = self.client.networks.create(self.public_network_name, driver="bridge")

        print(f"Creating internal network: {self.internal_network_name}")
        self.internal_network = self.client.networks.create(self.internal_network_name, driver="bridge")

        print("Starting internal DB container...")
        self.db_container = self.client.containers.run(
            f"{self.prefix}_db",
            name=f"{self.prefix}_db_{uuid.uuid4().hex[:8]}",
            network=self.internal_network_name,
            detach=True,
            tty=True
        )

        defender_ips = []
        for i in range(num_defenders):
            print(f"Starting defender container {i+1}/{num_defenders} on public network...")
            defender_container = self.client.containers.run(
                f"{self.prefix}_defender",
                name=f"{self.prefix}_defender_{uuid.uuid4().hex[:8]}",
                network=self.public_network_name,
                environment={"VULN_CHOICE": str(vuln_choice)},
                detach=True,
                tty=True
            )
            print(f"Connecting defender container {i+1} to internal network...")
            self.internal_network.connect(defender_container)
            self.defender_containers[f"defender_{i}"] = defender_container

        for i in range(num_attackers):
            print(f"Starting attacker container {i+1}/{num_attackers} on public network...")
            attacker_container = self.client.containers.run(
                f"{self.prefix}_attacker",
                name=f"{self.prefix}_attacker_{uuid.uuid4().hex[:8]}",
                network=self.public_network_name,
                detach=True,
                tty=True
            )
            self.attacker_containers[f"attacker_{i}"] = attacker_container

        # Inject the secret flag into the DB container
        flag_path = "/tmp/flag.txt"
        print(f"Injecting flag into internal DB container at {flag_path}...")
        command = f"bash -c 'echo \"{secret_flag}\" > {flag_path}'"
        self.db_container.exec_run(command)

        # Give the services a moment to start
        time.sleep(2)

        # Get IP addresses
        self.db_container.reload()

        for name, container in self.defender_containers.items():
            container.reload()
            ip = container.attrs['NetworkSettings']['Networks'][self.public_network_name]['IPAddress']
            defender_ips.append(ip)

        for name, container in self.attacker_containers.items():
            container.reload()

        return {
            "attacker_ids": {k: v.id for k, v in self.attacker_containers.items()},
            "defender_ids": {k: v.id for k, v in self.defender_containers.items()},
            "db_id": self.db_container.id,
            "defender_ips": defender_ips
        }

    def execute_in_container(self, agent_id: str, role: str, command: str) -> str:
        """Executes a bash command in the specified container and returns output."""
        import os
        if os.environ.get("MOCK_DOCKER_NO_CONTAINERS"):
            return f"MOCK OUTPUT: '{command}' executed successfully."

        container = self.attacker_containers.get(agent_id) if role == "attacker" else self.defender_containers.get(agent_id)
        if not container:
            return f"Error: Container for agent {agent_id} not running."

        try:
            # We use bash -c to support pipes and redirects if the agent tries to use them
            exec_result = container.exec_run(["bash", "-c", command])
            output = exec_result.output.decode('utf-8')
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
