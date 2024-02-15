import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, urljoin
import csv
import sys

#style terminal
from colorama import Fore, Back, Style

#bibliotecas para HTML renderizado
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_backend(url):

    # Realiza a requisição da página
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print('Erro ao acessar o site: ', e)
        quit()

    # Analisa o HTML da página com o BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Verifica se a página foi acessada com sucesso
    if response.status_code == 200:
        print(Fore.GREEN +'\n-----------Iniciando varredura...'+ Fore.RESET)
        def verificar_conteudo():
        
            print(Fore.BLUE +'\n-----------Analise de conteúdo...'+ Fore.RESET)
            # Verifica se existe o título da página e mostra a quantidade de caracteres
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.text.strip()
                title_length = len(title_text)
                print(f'Título encontrado com {title_length} caracteres: {title_text}')
            else:
                print('Não foi encontrado o título da página.')

            # Verifica se existe a descrição da página e mostra a quantidade de caracteres
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                desc_text = meta_desc.get('content').strip()
                desc_length = len(desc_text)
                print(f'Descrição encontrada com {desc_length} caracteres: {desc_text}')
            else:
                print('Não foi encontrada a descrição da página.')
                
        def verificar_responsividade(url):
            
            # Define as resoluções de tela a serem testadas
            resolutions = [(768, 1024), (1280, 800), (1440, 900)]

            # Define o navegador a ser utilizado
            driver = webdriver.Chrome()

            # Maximiza a janela do navegador
            driver.maximize_window()

            # Define um tempo limite para o carregamento da página
            driver.set_page_load_timeout(10)

            # Navega até a URL
            driver.get(url)
            
            print(Fore.BLUE +'\n-----------Analise do tempo de carregamento...'+ Fore.RESET)
            
            # Verifica o tempo de carregamento da página
            load_time = driver.execute_script("return performance.timing.loadEventEnd - performance.timing.navigationStart;")
            if load_time > 30000:
                print("A página demorou mais de 30 segundos para carregar.")
            else:
                print("A página carregou em menos de 30 segundos.")
                
            print(Fore.BLUE +'\n----------Analise de responsivide...'+ Fore.RESET)
            # Inicializa a variável para verificar a responsividade da página
            is_responsive = True

            # Verifica a responsividade da página para cada resolução de tela
            for width, height in resolutions:
                # Define a resolução da tela
                driver.set_window_size(width, height)

                try:
                    # Espera até que um elemento da página seja carregado
                    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))

                    # Verifica se o elemento está visível na tela
                    if not element.is_displayed():
                        is_responsive = False
                        print(f"Resolução de tela {width}x{height}: Elemento não visível na tela.")
                except:
                    is_responsive = False
                    print(f"Resolução de tela {width}x{height}: Nenhum elemento encontrado.")

            # Verifica se a página é responsiva
            if is_responsive:
                print("A página é responsiva.")
            else:
                print("A página não é responsiva.")
            
            # Fecha o navegador
            driver.quit()

        def verificar_rastreabilidade():
            print(Fore.BLUE +'\n----------Analise de rastreabilidade...'+ Fore.RESET)
            #verifica se a página esta sendo bloqueada pelo arquivo robots.txt
            def is_blocked_by_robots_txt(url):
                robots_url = urljoin(url, "/robots.txt")
                parsed_url = urlparse(url)
                response = requests.get(robots_url)
                
                if response.status_code == 200:
                    for line in response.text.split("\n"):
                        if line.startswith("Disallow:"):
                            disallowed_path = line.split(":")[1].strip()
                            if disallowed_path == "/" or parsed_url.path.startswith(disallowed_path):
                                print('Bloqueada pelo robots.txt')
                                return True                  
                print('Esta página não é bloqueada pelo robots.txt')
                return False
                
            is_blocked_by_robots_txt(url)
            
            # Verifica se a página tem tag canonical e se ela é self-referecing ou não
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical is not None:
                print(f'A página tem tag canonical apontando para {canonical["href"]}.')
                if canonical['href'] == url:
                    print('A tag canonical é self-referecing.')
                else:
                    print('A tag canonical não é self-referecing.')
            else:
                print('A página não possui tag canonical.')

            # Verifica se a página está indexada
            if 'noindex' in soup.find('meta', attrs={'name': 'robots'}).get('content').lower():
                print('A página não está indexada')
            else:
                print('A página é indexavel')

        def verificar_dados():
            print(Fore.BLUE +'\n----------Analise de dados estruturados...'+ Fore.RESET)
            # Verifica se existem dados estruturados
            structured_data_types = []
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    structured_data = json.loads(script.string)
                    if '@type' in structured_data:
                        structured_data_types.append(structured_data['@type'])
                except json.JSONDecodeError:
                    continue

            if structured_data_types:
                print('A página contém os seguintes tipos de dados estruturados:')
                for data_type in set(structured_data_types):
                    print('- ' + data_type)
            else:
                print('A página não contém dados estruturados')
            return structured_data_types
        
        links = soup.find_all('a')                    
        def count_unique_links(links, url):
            print(Fore.BLUE +'\n----------Analise de linkagem interna...'+ Fore.RESET)
            unique_links = []
            links_with_params = []
            broken_links = []
            redirect_links = []
            links_server_error = []

            parsed_base_url = urlparse(url)

            for link in links:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        href = urljoin(url, href)
                    elif not href.startswith('http'):
                        href = urljoin(parsed_base_url.scheme + "://" + parsed_base_url.netloc, href)

                    if href not in unique_links:
                        unique_links.append(href)

                    if '?' in href:
                        links_with_params.append(href)

                    try:
                        response = requests.head(href)
                        status_code = response.status_code
                        if status_code >= 300 and status_code < 400:
                            print(f"Redirect link found: {href} ({status_code})")
                            redirect_links.append(href)
                        elif status_code >= 400 and status_code < 500:
                            print(f"Client error link found: {href} ({status_code})")
                            broken_links.append(href)
                        elif status_code >= 500 and status_code < 600:
                            print(f"Server error link found: {href} ({status_code})")
                            links_server_error.append(href)
                    except requests.exceptions.RequestException:
                        print(f"Error connecting to link: {href}")

            unique_links_count = len(unique_links)
            links_with_params_count = len(links_with_params)
            broken_links_count = len(broken_links)
            redirect_links_count = len(redirect_links)
            links_server_error_count = len(links_server_error)
            

            print(f"A página possui {unique_links_count} links únicos.")
            print(f"{links_with_params_count} dos links contêm parâmetros de URL.")
            print(f"{redirect_links_count} dos links retornaram status 3xx")
            print(f"{broken_links_count} dos links retornaram status 4xx")
            print(f"{links_server_error_count} dos links retornaram status 5xx")

            return {"unique_links": unique_links_count, "links_with_params": links_with_params_count, "broken_links": broken_links_count, "redirect_links": redirect_links_count, "links_server_error": links_server_error_count}
        
        def check_images(url):
            images = soup.find_all('img')
            for img in images:
                alt = img.get('alt')
                if not alt:
                    print(f'A imagem {img["src"]} em {url} não tem atributo alt definido.')
                if img['src'].startswith(('http', 'https')):
                    try:
                        size = int(requests.head(img['src']).headers.get('content-length', 0))
                        if size > 100000:
                            print(f'A imagem {img["src"]} em {url} tem {size/1000:.1f} KB e precisa ser otimizada.')
                    except Exception as e:
                        print(f'Erro ao verificar a imagem {img["src"]}: {e}')
                elif img['src'] == '':
                    print(f'A imagem {img} em {url} não tem uma URL definida.')
                else:
                    print(f'A imagem {img["src"]} em {url} não pode ser verificada, pois não está hospedada em um servidor remoto.') 
                        
    else:
        print('Não foi possível acessar a página')

    verificar_rastreabilidade()
    structured_data_types = verificar_dados()
    verificar_conteudo()
    check_images(url)    
    verificar_responsividade(url)
    resultado = count_unique_links(links, url)


    #-------------------------------Relatorio de Melhorias-------------------------------------

    print(Fore.GREEN +'\n-----------Iniciando Auditoria...'+ Fore.RESET)
    def diagnostico_de_links(redirect_links, broken_links, links_server_error):
        if not redirect_links and not broken_links and not links_server_error:
            print('Nenhum erro relacionado a linkagem interna.')
        else:
            print("Segue lista de Erros relacionado a linkagem interna da páginas\n e possíveis melhorias a serem aplicadas:")
            if redirect_links:
                print(Fore.BLUE +'\nProblema identificado: Erros 3xx '+ Fore.RESET)
                print("Queda na frequencia de rastreamento, redução da autoridade da página e Impacto\n negativo na experiência do usuário devido a presença de redirecionamentos.")
                print(Fore.BLUE +'\nSolução:'+ Fore.RESET)
                print("- Remova os redirecionamentos internos presentes na página.")

            if broken_links:
                print(Fore.BLUE +'\nProblema: Erros 4xx '+ Fore.RESET)
                print("- Impacto: Experiência do usuário prejudicada e autoridade sendo dissipada, devido a presença de linkagem interna para páginas quebradas.")
                print(Fore.BLUE +'\nSolução:'+ Fore.RESET)
                print("- Remova as linkagens internas e redirecione os URLs quebrados")

            if links_server_error:
                print(Fore.BLUE +'\nProblema: Erros 3xx '+ Fore.RESET)
                print("- Impacto: Redução da autoridade e possível desindexação das páginas linkadas com erros 5xx.")
                print(Fore.BLUE +'\nSolução:'+ Fore.RESET)
                print("- Verifique se seu servidor esta passando por alguma instabilidade. Caso o problema persista apenas para estas páginas, substitua os URLs linkados.")
            
                # Exportar para CSV
            with open('relatorio_auditoria.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Tipo de Erro', 'Impacto', 'Solução'])

                if redirect_links:
                    writer.writerow(['Erros 3xx', 'Queda na frequência de rastreamento...', 'Remova os redirecionamentos internos presentes na página.'])

                if broken_links:
                    writer.writerow(['Erros 4xx', 'Experiência do usuário prejudicada e autoridade sendo dissipada...', 'Remova as linkagens internas e redirecione os URLs quebrados'])

                if links_server_error:
                    writer.writerow(['Erros 5xx', 'Redução da autoridade e possível desindexação...', 'Verifique se seu servidor está passando por alguma instabilidade.'])


    diagnostico_de_links(resultado["redirect_links"], resultado["broken_links"], resultado["links_server_error"])

    def diagnostico_dados_estruturados(structured_data_types):
        # Verifica se a página é um blog ou um site
        if 'blog.' in url or '/blog' in url:
            tipo_pagina = 'blog'
            dados_ideais = ['Article', 'BreadcrumbList', 'WebPage', 'FAQ', 'Person']
        else:
            tipo_pagina = 'site'
            dados_ideais = ['Organization', 'WebSite', 'SearchAction', 'BreadcrumbList', 'FAQ']

        # Verifica se a página possui todos os dados estruturados ideais para o tipo de página
        faltando = set(dados_ideais) - set(structured_data_types)
        if faltando:
            print(f'\nA página ainda não contém os seguintes dados estruturados. \nExperimente coloca-los pois são ideais para páginas de {tipo_pagina}: ') 
            for data_type in faltando:    
                print('- ' + data_type)
                
        else:
            print(f'\nSua página contém todos os dados estruturados ideais para {tipo_pagina}.')
        
            # Exportar para CSV
        with open('relatorio_auditoria.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([])  # Adiciona uma linha em branco para separar os dois diagnósticos
            writer.writerow(['Tipo de Dado Faltante', 'Descrição'])

            for data_type in faltando:
                writer.writerow([data_type, f'Dados estruturados ideais para páginas de {tipo_pagina} estão faltando.'])

    # Chama função
    diagnostico_dados_estruturados(structured_data_types)
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python pagescan.py <URL>")
    else:
        url = sys.argv[1]
        run_backend(url)