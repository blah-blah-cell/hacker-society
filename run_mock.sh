python src/mock_llm_server.py &
sleep 2
MOCK_DOCKER_NO_CONTAINERS=1 python src/main.py --model mock-model --base-url http://localhost:8000/v1 --attackers 1 --defenders 1 --turns 1 <<EOM
1
EOM
