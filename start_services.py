import os
import sys
import time
import subprocess
import platform
import json
from pathlib import Path

DOCKER_COMPOSE_FILE = "docker-compose.yml"

WAIT_TIME_SECONDS = 20
CHECK_DOCKER_TIMEOUT = 10
KAFKA_TOPICS = [
    {"name": "raw-comments", "partitions": 3, "replication_factor": 1},
    {"name": "clean-comments", "partitions": 3, "replication_factor": 1},
    {"name": "sentiment-results", "partitions": 3, "replication_factor": 1},
]
SERVICE_PORTS = {"kafka": 9092, "redis": 6379, "storm_ui": 8080, "zookeeper": 2181}
APP_COMPONENTS = [
    {
        "name": "YouTube comment ingestion",
        "command": "python ingestion/youtube_api.py",
    },
    {
        "name": "Sentiment analysis",
        "command": "python processing/sentiment_analyzer.py",
    },
    {
        "name": "Comment summarization",
        "command": "python processing/comment_summarizer.py",
    },
    {"name": "Dashboard", "command": "streamlit run dashboard/dashboard.py"},
]
ENABLE_COLORS = platform.system().lower() != "windows"


class Colors:
    if ENABLE_COLORS:
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        WHITE = "\033[97m"
        BOLD = "\033[1m"
        END = "\033[0m"
    else:
        GREEN = YELLOW = RED = CYAN = WHITE = BOLD = END = ""


class ServiceManager:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.docker_compose_file = self.script_dir / DOCKER_COMPOSE_FILE
        self.platform = platform.system().lower()
        self.user_name = os.environ.get("USERNAME", os.environ.get("USER", "user"))

    def print_colored(self, message, color=Colors.WHITE):
        print(f"{color}{message}{Colors.END}")

    def print_header(self):
        self.print_colored("=" * 60, Colors.CYAN)
        self.print_colored("🚀 YouTube Live Stream Analytics System", Colors.GREEN)
        self.print_colored("=" * 60, Colors.CYAN)
        self.print_colored(f"👤 User: {self.user_name}", Colors.WHITE)
        self.print_colored(f"📁 Directory: {self.script_dir}", Colors.WHITE)
        self.print_colored(
            f"💻 Platform: {platform.system()} {platform.release()}", Colors.WHITE
        )
        self.print_colored(f"🐍 Python: {sys.version.split()[0]}", Colors.WHITE)
        self.print_colored("=" * 60, Colors.CYAN)

    def run_command(self, command, shell=True, capture_output=False, timeout=None):
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=shell,
                    capture_output=True,
                    text=True,
                    cwd=self.script_dir,
                    timeout=timeout,
                )
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command, shell=shell, cwd=self.script_dir, timeout=timeout
                )
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)

    def check_docker_running(self):
        self.print_colored("🔍 Checking Docker status...", Colors.YELLOW)

        success, stdout, stderr = self.run_command("docker info", capture_output=True)

        if success:
            self.print_colored("✅ Docker is running", Colors.GREEN)
            return True
        else:
            self.print_colored(
                "❌ Docker is not running. Please start Docker first.", Colors.RED
            )
            self.print_colored(f"Error: {stderr}", Colors.RED)
            return False

    def check_docker_compose(self):
        if not self.docker_compose_file.exists():
            self.print_colored(
                f"❌ docker-compose.yml not found in {self.script_dir}", Colors.RED
            )
            return False
        return True

    def start_infrastructure_services(self):
        self.print_colored(
            "📦 Starting infrastructure services (Kafka, Redis, Storm)...",
            Colors.YELLOW,
        )

        compose_commands = ["docker-compose", "docker compose"]
        compose_cmd = None

        for cmd in compose_commands:
            success, _, _ = self.run_command(f"{cmd} --version", capture_output=True)
            if success:
                compose_cmd = cmd
                break

        if not compose_cmd:
            self.print_colored(
                "❌ Neither 'docker-compose' nor 'docker compose' found!", Colors.RED
            )
            return False

        success, stdout, stderr = self.run_command(f"{compose_cmd} up -d")
        if success:
            self.print_colored("✅ Docker services started successfully", Colors.GREEN)
            return True
        else:
            self.print_colored(
                f"❌ Failed to start Docker services: {stderr}", Colors.RED
            )
            return False

    def wait_for_services(self, wait_time=None):
        if wait_time is None:
            wait_time = WAIT_TIME_SECONDS

        self.print_colored(
            f"⏳ Waiting {wait_time} seconds for services to start...", Colors.YELLOW
        )

        for i in range(wait_time):
            if i % 5 == 0:
                remaining = wait_time - i
                self.print_colored(
                    f"   ⏰ {remaining} seconds remaining...", Colors.WHITE
                )
            time.sleep(1)

    def create_kafka_topics(self):
        self.print_colored("� Creating Kafka topics...", Colors.YELLOW)

        success, container_id, stderr = self.run_command(
            "docker ps -q -f name=kafka", capture_output=True, timeout=10
        )

        if not success or not container_id.strip():
            self.print_colored("❌ Kafka container not found", Colors.RED)
            self.print_colored(
                "ℹ️  This might be normal if using external Kafka", Colors.YELLOW
            )
            return True

        container_id = container_id.strip().split("\n")[0]

        for topic_config in KAFKA_TOPICS:
            topic_name = topic_config["name"]
            partitions = topic_config["partitions"]
            replication_factor = topic_config["replication_factor"]

            cmd = (
                f"docker exec {container_id} kafka-topics --create --topic {topic_name} "
                f"--bootstrap-server localhost:9092 --partitions {partitions} "
                f"--replication-factor {replication_factor} --if-not-exists"
            )

            success, stdout, stderr = self.run_command(
                cmd, capture_output=True, timeout=20
            )

            if success:
                self.print_colored(
                    f"✅ Topic '{topic_name}' created/verified", Colors.GREEN
                )
            else:
                self.print_colored(
                    f"⚠️  Warning: Could not create topic '{topic_name}': {stderr}",
                    Colors.YELLOW,
                )

        return True

    def check_service_health(self):
        self.print_colored("🔍 Checking service health...", Colors.YELLOW)

        services_to_check = [
            ("Kafka", "localhost:9092"),
            ("Redis", "localhost:6379"),
            ("Storm UI", "localhost:8080"),
        ]

        success, stdout, stderr = self.run_command(
            "docker ps --format 'table {{.Names}}\t{{.Status}}'", capture_output=True
        )

        if success:
            self.print_colored("📊 Running containers:", Colors.CYAN)
            self.print_colored(stdout, Colors.WHITE)

        return True

    def print_service_status(self):
        self.print_colored("\n📊 Services Status:", Colors.CYAN)
        for service, port in SERVICE_PORTS.items():
            if service == "storm_ui":
                self.print_colored(f"- Storm UI: http://localhost:{port}", Colors.WHITE)
            elif service == "kafka":
                self.print_colored(f"- Kafka: localhost:{port}", Colors.WHITE)
            else:
                self.print_colored(
                    f"- {service.capitalize()}: localhost:{port}", Colors.WHITE
                )

    def check_python_requirements(self):
        requirements_file = self.script_dir / "requirements.txt"

        if requirements_file.exists():
            self.print_colored("📋 Checking Python requirements...", Colors.YELLOW)

            success, _, _ = self.run_command("pip --version", capture_output=True)
            if not success:
                self.print_colored(
                    "⚠️  pip not found. Please install pip first.", Colors.YELLOW
                )
                return False

            in_venv = hasattr(sys, "real_prefix") or (
                hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
            )

            if not in_venv:
                self.print_colored(
                    "💡 Tip: Consider using a virtual environment:", Colors.CYAN
                )
                if self.platform == "windows":
                    self.print_colored("   python -m venv venv", Colors.WHITE)
                    self.print_colored("   venv\\Scripts\\activate", Colors.WHITE)
                else:
                    self.print_colored("   python3 -m venv venv", Colors.WHITE)
                    self.print_colored("   source venv/bin/activate", Colors.WHITE)
                self.print_colored("   pip install -r requirements.txt", Colors.WHITE)

        return True

    def start_system(self):
        self.print_header()

        if not self.check_docker_compose():
            return False

        if not self.check_docker_running():
            return False

        self.check_python_requirements()

        if not self.start_infrastructure_services():
            return False

        self.wait_for_services(WAIT_TIME_SECONDS)

        self.create_kafka_topics()

        self.check_service_health()

        self.print_colored(
            "\n✅ Infrastructure services started successfully!", Colors.GREEN
        )
        self.print_service_status()
        return True


def main():
    try:
        service_manager = ServiceManager()
        success = service_manager.start_system()

        if success:
            service_manager.print_colored(
                "\n🎉 System startup completed successfully!", Colors.GREEN
            )
            return 0
        else:
            service_manager.print_colored("\n❌ System startup failed!", Colors.RED)
            return 1

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Startup interrupted by user{Colors.END}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
