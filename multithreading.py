import requests
import time
import csv
import random
from multiprocessing import Process
import threading
import concurrent.futures
from bs4 import BeautifulSoup

# Definindo cabeçalhos (headers) para a requisição HTTP
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}
MAX_THREADS = 10  # Número máximo de threads
MAX_PROCESSES = 4  # Número máximo de processos

# Função para extrair detalhes de um filme a partir de um link
def extract_movie_details(movie_link):
    # Espera um tempo aleatório para evitar ser bloqueado pelo servidor
    time.sleep(random.uniform(0, 0.2))
    # Faz uma requisição HTTP ao link do filme
    response = requests.get(movie_link, headers=headers)
    # Cria um objeto BeautifulSoup para analisar o HTML da página
    movie_soup = BeautifulSoup(response.content, 'html.parser')

    # Verifica se a página foi carregada corretamente
    if movie_soup is not None:
        title, date, rating, plot_text = None, None, None, None

        # Encontra a seção específica que contém as informações do filme
        page_section = movie_soup.find('section', attrs={'class': 'ipc-page-section'})
        if page_section is not None:
            # Busca as divs dentro da seção
            divs = page_section.find_all('div', recursive=False)

            if len(divs) > 1:
                target_div = divs[1]

                # Busca o título do filme
                title_tag = target_div.find('h1')
                if title_tag:
                    title = title_tag.find('span').get_text()

                # Busca a data de lançamento do filme
                date_tag = target_div.find('a', href=lambda href: href and 'releaseinfo' in href)
                if date_tag:
                    date = date_tag.get_text().strip()

                # Busca a classificação do filme (rating)
                rating_tag = movie_soup.find('div', attrs={'data-testid': 'hero-rating-bar__aggregate-rating__score'})
                rating = rating_tag.get_text() if rating_tag else None

                # Busca a sinopse do filme
                plot_tag = movie_soup.find('span', attrs={'data-testid': 'plot-xs_to_m'})
                plot_text = plot_tag.get_text().strip() if plot_tag else None

                # Armazena os dados do filme no arquivo CSV
                with open('movies.csv', mode='a', newline='', encoding='utf-8') as file:
                    movie_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    if all([title, date, rating, plot_text]):
                        movie_writer.writerow([title, date, rating, plot_text])

# Função para extrair os links dos filmes da página principal
def extract_movies():
    # Faz a requisição HTTP para a página dos filmes mais populares
    response = requests.get('https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm', headers=headers)
    # Cria um objeto BeautifulSoup para analisar o HTML da página
    soup = BeautifulSoup(response.content, 'html.parser')
    # Encontra a tabela que contém a lista de filmes
    movies_table = soup.find('div', attrs={'data-testid': 'chart-layout-main-column'}).find('ul')
    # Encontra todas as linhas da tabela (cada filme)
    movies_table_rows = movies_table.find_all('li')
    # Extrai os links de cada filme e adiciona a lista
    movie_links = ['https://imdb.com' + movie.find('a')['href'] for movie in movies_table_rows]
    return movie_links

# Função para usar multithreading para extrair detalhes dos filmes
def use_threads(movie_links):
    # Define o número de threads a serem utilizadas
    threads = min(MAX_THREADS, len(movie_links))
    # Usa ThreadPoolExecutor para executar várias threads simultaneamente
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(extract_movie_details, movie_links)

# Função para usar multiprocessing para extrair detalhes dos filmes
def use_processes(movie_links):
    processes = []
    # Inicia processos para cada link, limitando ao número máximo de processos
    for link in movie_links[:MAX_PROCESSES]:
        process = Process(target=extract_movie_details, args=(link,))
        processes.append(process)
        process.start()

    # Aguarda todos os processos terminarem
    for process in processes:
        process.join()

# Função para comparar o tempo de execução entre threading e multiprocessing
def compare_execution_times():
    # Extrai os links dos filmes
    movie_links = extract_movies()

    # Medindo o tempo de execução usando threading
    start_thread_time = time.time()  # Início da contagem do tempo
    use_threads(movie_links)  # Executa a função que utiliza threading
    end_thread_time = time.time()  # Fim da contagem do tempo
    print(f"Threading Time: {end_thread_time - start_thread_time} seconds")  # Exibe o tempo total de execução

    # Medindo o tempo de execução usando multiprocessing
    start_process_time = time.time()  # Início da contagem do tempo
    use_processes(movie_links)  # Executa a função que utiliza multiprocessing
    end_process_time = time.time()  # Fim da contagem do tempo
    print(f"Multiprocessing Time: {end_process_time - start_process_time} seconds")  # Exibe o tempo total de execução

# Executa o script principal
if __name__ == '__main__':
    compare_execution_times()
