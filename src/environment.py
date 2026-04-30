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

        self.attacker_container = None
        self.defender_container = None
        self.db_container = None

    def setup(self, secret_flag: str, vuln_choice: int):
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

        print("Starting defender container on public network...")
        self.defender_container = self.client.containers.run(
            f"{self.prefix}_defender",
            name=f"{self.prefix}_defender_{uuid.uuid4().hex[:8]}",
            network=self.public_network_name,
            environment={"VULN_CHOICE": str(vuln_choice)},
            detach=True,
            tty=True
        )

        print("Connecting defender container to internal network...")
        self.internal_network.connect(self.defender_container)

        print("Starting attacker container on public network...")
        self.attacker_container = self.client.containers.run(
            f"{self.prefix}_attacker",
            name=f"{self.prefix}_attacker_{uuid.uuid4().hex[:8]}",
            network=self.public_network_name,
            detach=True,
            tty=True
        )

        # Inject the secret flag into the DB container
        flag_path = "/tmp/flag.txt"
        print(f"Injecting flag into internal DB container at {flag_path}...")
        command = f"bash -c 'echo \"{secret_flag}\" > {flag_path}'"
        self.db_container.exec_run(command)

        # Give the services a moment to start
        time.sleep(2)

        # Get IP addresses
        self.defender_container.reload()
        self.attacker_container.reload()
        self.db_container.reload()

        defender_ip = self.defender_container.attrs['NetworkSettings']['Networks'][self.public_network_name]['IPAddress']

        return {
            "attacker_id": self.attacker_container.id,
            "defender_id": self.defender_container.id,
            "db_id": self.db_container.id,
            "defender_ip": defender_ip
        }

    def execute_in_container(self, role: str, command: str) -> str:
        """Executes a bash command in the specified container and returns output."""
        container = self.attacker_container if role == "attacker" else self.defender_container
        if not container:
            return "Error: Container not running."

        try:
            # We use bash -c to support pipes and redirects if the agent tries to use them
            exec_result = container.exec_run(["bash", "-c", command])
            output = exec_result.output.decode('utf-8')
            return output if output else f"Command '{command}' executed successfully with no output."
        except Exception as e:
            return f"Execution error: {str(e)}"

    def teardown(self):
        print("Tearing down environment...")
        if self.attacker_container:
            try:
                self.attacker_container.stop(timeout=1)
                self.attacker_container.remove()
                print("Attacker container removed.")
            except Exception as e:
                print(f"Error removing attacker: {e}")

        if self.defender_container:
            try:
                self.defender_container.stop(timeout=1)
                self.defender_container.remove()
                print("Defender container removed.")
            except Exception as e:
                print(f"Error removing defender: {e}")

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
