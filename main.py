# Scraper do OJogoDoBicho.Net
# Autores: Matheus Pestana (matheus.pestana@iesp.uerj.br)

import warnings
from os.path import exists

import click
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

login_page = "https://www.ojogodobicho.net/modules.php?name=Your_Account"
deu_no_poste = "https://www.ojogodobicho.net/modules.php?name=Postetudo&page="
busca_milhar = "https://www.ojogodobicho.net/modules.php?name=Milhar"

# Para ignorar os warnings...
warnings.simplefilter(action='ignore', category=FutureWarning)

# Xpaths
xpath_ano = "/html/body/table[1]/tbody/tr/td/table[4]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table"
xpath_milhar = "/html/body/table[1]/tbody/tr/td/table[4]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/form/center/center[1]"
xpath_totalpaginas = "/html/body/table[1]/tbody/tr/td/table[4]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/div/font"

print('''
Bem-vindo(a) ao RaspaBicho! 
Criado por Mateus Pestana em 03/05/2022
Esse scraper baixa os resultados dos últimos 365 dias
do jogo do bicho no Rio de Janeiro. 

Para prosseguir, digite seu login e senha de "OJogoDoBicho.Net" :
''')
login = input("Usuário:  ")
senha = input("Senha:  ")

caminho = click.prompt("Qual o caminho do arquivo já salvo/a ser salvo?", type=str,
                       default="~/Downloads/")

metodo = click.prompt("Qual a raspagem?", type=str,
                      default="ano") # TODO: alterar nome da variável


def install_chrome():
    print("Abrindo navegador...")
    s = Service(ChromeDriverManager().install())
    global driver # TODO resolver essa coisa do driver global
    global options
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=s, options=options)
    print("Carregando página de login...")
    driver.get(login_page)
    return driver


def faz_login(login, senha):
    username = driver.find_element(By.NAME, 'username')
    password = driver.find_element(By.NAME, 'user_password')

    print("Fazendo o login...")
    username.send_keys(login)
    password.send_keys(senha)
    password.send_keys(Keys.RETURN)
    print("Login feito!\n\n")


def raspa_tabela_ano():
    if exists(caminho + "diarios.csv"):
        print("Arquivo já existe! Abrindo...")
        global existe # TODO: resolver esse existe global
        existe = True
        resultados = pd.read_csv(caminho, header=0, index_col=None).drop_duplicates()
    else:
        print("Arquivo não existe! Criando base...")
        existe = False
        resultados = pd.DataFrame()

    print("Iniciando a raspagem:")
    paginas_totais = checa_total_pages()

    for pagina in np.arange(1, paginas_totais):
        print(f"Baixando da página {pagina}/{str(paginas_totais - 1)}")
        driver.get(deu_no_poste + str(pagina))
        tabela = driver.find_element(By.XPATH,
                                     xpath_ano)
        tabela = tabela.get_attribute('innerHTML')
        tabela = pd.read_html(tabela, match='DIA')
        if existe:
            tabela[0].columns = resultados.columns # TODO: definir as variáveis na mão
            resultados = resultados.append(tabela[0], ignore_index=True)
        else:
            resultados = resultados.append(tabela[0], ignore_index=True)

    print("Todas as páginas baixadas!")
    if existe:
        pass
    else:
        print("Preparando para limpar os dados...")
        resultados.columns = ['DIA', 'DATA', 'TIPO', '1 P', '2 P', '3 P', '4 P', '5 P', '6 P', '7 P']

    resultados = resultados.drop_duplicates()
    resultados = resultados[resultados.DIA != "DIA"]

    print("Salvando em CSV...")
    resultados.to_csv(caminho + "diarios.csv", index=False)
    print("Tudo certo! Tchau!")
    driver.quit()


def checa_total_pages():
    driver.get(deu_no_poste + str(1))
    pag_max = driver.find_element(By.XPATH, xpath_totalpaginas)
    pag_max = int(BeautifulSoup(pag_max.get_attribute('innerHTML'), 'lxml').text.split(sep='|')[-2])
    return pag_max + 1


def raspa_milhar():
    vetor_milhar = ["%04d" % i for i in np.arange(1, 10000)]

    milhares = pd.DataFrame()

    for numero_milhar in vetor_milhar:
        driver.get(busca_milhar)
        campo_milhar = driver.find_element(By.NAME, "milhar")

        campo_milhar.send_keys(numero_milhar)
        campo_milhar.send_keys(Keys.RETURN)
        print(f"Baixando milhar {numero_milhar}...")
        milhar = driver.find_element(By.XPATH, xpath_milhar)
        milhar = milhar.get_attribute('innerHTML')
        milhar = pd.read_html(milhar, match='MILHAR')
        milhares = milhares.append(milhar, ignore_index=True)

    milhares.columns = ['MILHAR', 'TIPO', 'PREMIO', 'DATA']
    milhares.drop_duplicates(inplace=True)
    milhares = milhares[milhares.MILHAR != "MILHAR"] #TODO: salvar a coluna como string pra não perder os 0 iniciais
    print("Salvando em CSV...")
    milhares.to_csv(caminho + "milhares.csv")
    driver.quit()


def main(): # TODO: acertar o main pra não precisar chamar main() depois
    install_chrome()
    faz_login(login, senha)
    if metodo == "ano":
        raspa_tabela_ano() # TODO: salvar cada função num arquivo diferente
    elif metodo == "milhar":
        raspa_milhar() # TODO: implementar centenas e dezenas
    else:
        print("Você não escolheu um método válido")
        driver.quit()


main()
