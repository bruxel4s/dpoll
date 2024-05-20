from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import hashlib

app = Flask(__name__)




@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fotoma/<cpf>', methods=['GET'])
def fotoma(cpf):
    dados = consultar_cpf(cpf)
    return jsonify(dados)

def consultar_cpf(cpf):
    login_url = 'https://sigma.policiacivil.ma.gov.br/'
    login_data = {
        'username': '386.482.373-00',
        'password': 'Rabelo@#676069'
    }
    
    consulta_url = 'https://sigma.policiacivil.ma.gov.br/pessoas/lista/resultado/consulta/individuo'
    session = requests.Session()
    response = session.post(login_url, data=login_data)

    if response.status_code != 200:
        return {"error": f"Erro ao realizar o login: {response.status_code}"}

    consulta_params = {
        'nome': '',
        'cpf': cpf,
        'nomeMae': '',
        'nomePai': '',
        'dddCelular': '',
        'telefoneCelular': '',
        'dddFixo': '',
        'telefoneFixo': ''
    }

    consulta_response = session.get(consulta_url, params=consulta_params)

    if consulta_response.status_code == 200:
        soup = BeautifulSoup(consulta_response.text, 'html.parser')
        link_segunda_consulta = soup.find('a', href=lambda href: href and '/pessoas/resultado/especifico/consulta/individuo/' in href)
        
        if link_segunda_consulta:
            link_segunda_consulta = 'https://sigma.policiacivil.ma.gov.br' + link_segunda_consulta['href']
            segunda_consulta_response = session.get(link_segunda_consulta)
            
            if segunda_consulta_response.status_code == 200:
                soup_segunda_consulta = BeautifulSoup(segunda_consulta_response.text, 'html.parser')

                img_tag = soup_segunda_consulta.find('img', class_='img-thumbnail preview-img')
                
                if img_tag:
                    foto_url = img_tag['src']
                    foto_base64 = foto_url.split(',')[1] if ',' in foto_url else "SEM INFORMAÇÃO"
                else:
                    foto_base64 = "SEM INFORMAÇÃO"

                result = {
                    "foto": foto_base64,
                    "cpf": cpf,
                }

                return result
            else:
                return {"error": f"Erro ao fazer a segunda consulta: {segunda_consulta_response.status_code}"}
        else:
            return {"error": "Link para a segunda consulta não encontrado."}
    else:
        return {"error": f"Erro ao fazer a primeira consulta: {consulta_response.status_code}"}
    return None

@app.route('/sis/<cpf>', methods=['GET'])
def sis(cpf):
    dados = consulta(cpf)
    return jsonify(dados)

def generate_sha256_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def login(session):
    usuario = 'isis.mathiascoord'
    senha_original = '15102430'
    senha_hash = generate_sha256_hash(senha_original)
    login_url = 'https://sisregiii.saude.gov.br/'
    login_headers = {
        'Host': 'sisregiii.saude.gov.br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="124", "Android WebView";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'Upgrade-Insecure-Requests': '1',
        'Origin': 'https://sisregiii.saude.gov.br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-A022M Build/RP1A.200720.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6328.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://sisregiii.saude.gov.br/cgi-bin/index',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': 'TS019395b4=0140e3e4e596aa60819104086782492e91c3ce1b920d77f9712f46ac8250f2cdc66bca7dbc59fe002e45157c7a368c9358ce7ff2e6; SESSION=80d2c6cac9810894da129a04c2bf0644d62aeb07562b3641622d889cc5ee4073; ID=301389'
    }
    login_data = {
        'usuario': usuario,
        'senha': '',
        'senha_256': senha_hash,
        'etapa': 'ACESSO',
        'logout': ''
    }
    session.post(login_url, headers=login_headers, data=login_data)

def extrair_valor(tabela, campo):
    for row in tabela.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) > 1 and campo in columns[0].text:
            return columns[1].text.strip()
    return None

def extrair_valor_abaixo(tabela, campo):
    encontrado = False
    for row in tabela.find_all('tr'):
        columns = row.find_all('td')
        for col in columns:
            if encontrado:
                return col.text.strip()
            if campo in col.text:
                encontrado = True
    return None

def consulta(cpf):
    session = requests.Session()
    login(session)
    cpf_url = 'https://sisregiii.saude.gov.br/cgi-bin/cadweb50?standalone=1'
    cpf_data = {
        'nu_cns': cpf,
        'nome_paciente': '',
        'nome_mae': '',
        'dt_nascimento': '',
        'uf_nasc': '',
        'mun_nasc': '',
        'uf_res': '',
        'mun_res': '',
        'sexo': '',
        'etapa': 'DETALHAR',
        'url': '',
        'standalone': '1'
    }
    response = session.post(cpf_url, data=cpf_data)
    soup = BeautifulSoup(response.text, 'html.parser')
    tabela = soup.find('table', class_='table_listagem')

    if not tabela:
        return {}

    dados = {
        "cns": extrair_valor_abaixo(tabela, "CNS:"),
        "cpf": extrair_valor_abaixo(tabela, "CPF:"),
        "nome": extrair_valor_abaixo(tabela, "Nome Social / Apelido:"),
        "nome_mae": extrair_valor_abaixo(tabela, "Nome do Pai:"),
        "nome_pai": "N/A",
        "sexo": extrair_valor_abaixo(tabela, "Raça:"),
        "data_de_nascimento": extrair_valor_abaixo(tabela, "Tipo Sanguíneo:"),
        "nacionalidade": extrair_valor_abaixo(tabela, "Município de Nascimento:"),
        "bairro": extrair_valor_abaixo(tabela, "CEP:"),
        "pais_de_residencia": extrair_valor_abaixo(tabela, "Município de Residência:")
    }

    session.close()
    return dados


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)