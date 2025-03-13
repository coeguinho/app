from flask import Flask, render_template, jsonify
import requests
import base64
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# Configurações
host = '45.189.16.4'
url = f"https://ixc.mundonetbandalarga.com.br/webservice/v1/su_oss_chamado"
token = "15:9da60ceca34e3216604ce3aeb3ed2e55dad35888f57db09616b737bb4dcc1c04".encode('utf-8')

# Dicionário de mapeamento de técnicos (id_tecnico: nome)
tecnicos_map = {
    8: "Higor",
    21: "Romário",
    56: "Wenner",
    43: "Ivaldo",
    49: "Wallace",
    4: "Moises",
    22: "Silvan",
    57: "Rafael",
    60: "Julio",
    86: "Wladimir",
    39: "Walterlyno",
}

# Dicionário de mapeamento de status
status_map = {
    'EX': 'Em Execução',
    'DS': 'Em Deslocamento',
    'AG': 'Agendada',
    # Adicione outros status conforme necessário
}

# Função para buscar O.S por status e filtrar por data de hoje (se necessário)
def buscar_os_por_status(status, filtrar_por_data=False):
    payload = {
        'qtype': 'su_oss_chamado.status',  # Campo para filtrar
        'query': status,  # Status da O.S
        'oper': '=',  # Operador de comparação
        'page': '1',  # Página atual
        'rp': '20',  # Quantidade de registros por página
        'sortname': 'su_oss_chamado.id',  # Campo para ordenar
        'sortorder': 'asc'  # Ordem crescente
    }

    headers = {
        'ixcsoft': 'listar',
        'Authorization': f'Basic {base64.b64encode(token).decode("utf-8")}',
        'Content-Type': 'application/json'
    }

    # Fazendo a requisição
    response = requests.post(url, json=payload, headers=headers)

    # Processando a resposta
    if response.status_code == 200:
        os_list = response.json().get('registros', [])
        if filtrar_por_data:
            # Filtrar O.S agendadas para o dia atual
            hoje = datetime.now().strftime('%d-%m-%Y')  # Formato da data: DD-MM-YYYY
            os_list = [os for os in os_list if os.get('data_agendamento', '').startswith(hoje)]
        return os_list
    else:
        return []

from flask import Flask, render_template

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

# Nova rota para fornecer dados das O.S e técnicos disponíveis em JSON
@app.route('/api/os')
def api_os():
    # Buscar O.S em Execução (status = 'EX')
    os_execucao = buscar_os_por_status('EX')
    # Buscar O.S Em Deslocamento (status = 'DS')
    os_deslocamento = buscar_os_por_status('DS')
    # Buscar O.S Agendadas (status = 'AG') e filtrar por data de hoje
    os_agendadas = buscar_os_por_status('AG', filtrar_por_data=True)

    # Filtrar O.S sem técnico
    os_execucao = [os for os in os_execucao if os.get('id_tecnico') and int(os.get('id_tecnico')) != 0]
    os_deslocamento = [os for os in os_deslocamento if os.get('id_tecnico') and int(os.get('id_tecnico')) != 0]
    os_agendadas = [os for os in os_agendadas if os.get('id_tecnico') and int(os.get('id_tecnico')) != 0]

    # Lista de técnicos ocupados (com O.S em execução ou deslocamento)
    tecnicos_ocupados = set()
    for os in os_execucao + os_deslocamento:
        tecnicos_ocupados.add(int(os.get('id_tecnico')))

    # Lista de técnicos disponíveis
    tecnicos_disponiveis = []
    for id_tecnico, nome in tecnicos_map.items():
        tecnicos_disponiveis.append({
            'id': id_tecnico,
            'nome_tecnico': nome,
            'status': 'Técnico Ocupado' if id_tecnico in tecnicos_ocupados else 'Técnico Disponível',
            'icone': '⛔' if id_tecnico in tecnicos_ocupados else '✅'
        })

    # Verificar se todos os técnicos estão disponíveis
    todos_disponiveis = len(tecnicos_ocupados) == 0

    # Adicionar ícones, mapear técnicos, traduzir status e adicionar emoji de localização
    for os in os_execucao:
        os['nome_tecnico'] = tecnicos_map.get(int(os.get('id_tecnico')), 'Técnico Desconhecido')
        os['icone'] = '⚙️'  # Ícone para O.S em execução
        os['status'] = status_map.get(os.get('status'), os.get('status'))  # Traduz o status
        os['endereco'] = f"📍 {os.get('endereco', '')}"  # Adiciona emoji de localização
        os['id_assunto'] = os.get('id_assunto', 'N/A')  # Retorna o id_assunto diretamente

    for os in os_deslocamento:
        os['nome_tecnico'] = tecnicos_map.get(int(os.get('id_tecnico')), 'Técnico Desconhecido')
        os['icone'] = '🚗'  # Ícone para O.S em deslocamento
        os['status'] = status_map.get(os.get('status'), os.get('status'))  # Traduz o status
        os['endereco'] = f"📍 {os.get('endereco', '')}"  # Adiciona emoji de localização
        os['id_assunto'] = os.get('id_assunto', 'N/A')  # Retorna o id_assunto diretamente

    # Retornar os dados em JSON
    return jsonify({
        'os_execucao': os_execucao,
        'os_deslocamento': os_deslocamento,
        'tecnicos_disponiveis': tecnicos_disponiveis,
        'todos_disponiveis': todos_disponiveis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
