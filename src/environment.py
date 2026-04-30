import docker
import uuid
import time

class Environment:
    def __init__(self, prefix="hacker_society"):
        self.client = docker.from_env()
        self.prefix = prefix
        self.network_name = f"{self.prefix}_net_{uuid.uuid4().hex[:8]}"
        self.network = None
        self.attacker_container = None
        self.defender_container = None

    def setup(self, secret_flag: str):
        print("Building images...")
        self.client.images.build(path="./docker", dockerfile="Dockerfile.attacker", tag=f"{self.prefix}_attacker")
        self.client.images.build(path="./docker", dockerfile="Dockerfile.defender", tag=f"{self.prefix}_defender")

        print(f"Creating network: {self.network_name}")
        self.network = self.client.networks.create(self.network_name, driver="bridge")

        print("Starting defender container...")
        self.defender_container = self.client.containers.run(
            f"{self.prefix}_defender",
            name=f"{self.prefix}_defender_{uuid.uuid4().hex[:8]}",
            network=self.network_name,
            detach=True,
            tty=True
        )

        print("Starting attacker container...")
        self.attacker_container = self.client.containers.run(
            f"{self.prefix}_attacker",
            name=f"{self.prefix}_attacker_{uuid.uuid4().hex[:8]}",
            network=self.network_name,
            detach=True,
            tty=True
        )

        # Inject the secret flag into the defender container
        # Note: In a real scenario, this might be more complex, but for Phase 1 we write it to a file.
        flag_path = "/tmp/flag.txt"
        print(f"Injecting flag into defender container at {flag_path}...")

        # We can use 'exec_run' to echo the string into a file
        # Safe to do since we control secret_flag and the environment
        command = f"bash -c 'echo \"{secret_flag}\" > {flag_path}'"
        self.defender_container.exec_run(command)

        # Give the server a moment to start
        time.sleep(2)

        # Get IP addresses
        self.defender_container.reload()
        self.attacker_container.reload()

        defender_ip = self.defender_container.attrs['NetworkSettings']['Networks'][self.network_name]['IPAddress']

        return {
            "attacker_id": self.attacker_container.id,
            "defender_id": self.defender_container.id,
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

        if self.network:
            try:
                self.network.remove()
                print("Network removed.")
            except Exception as e:
                print(f"Error removing network: {e}")
