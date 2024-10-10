import os
import pickle  # Import da biblioteca padrão
import cv2  # Imports de terceiros
import numpy as np
from flask import Flask, render_template, Response

# Configurar o Flask para usar a pasta 'assets' como pasta de arquivos estáticos
app = Flask(__name__, static_folder='assets')

# Verifica se o arquivo vacancies.pkl existe e o carrega
if os.path.exists('vacancies.pkl'):
    with open('vacancies.pkl', 'rb') as archive:
        vacancies = pickle.load(archive)
else:
    vacancies = []
    print("Arquivo vacancies.pkl não encontrado!")

# Função para gerar quadros do vídeo com OpenCV
def generate_frames(): 
    # Verifica se o arquivo de vídeo existe
    if not os.path.exists('video.mp4'):
        print("Arquivo de vídeo video.mp4 não encontrado!")
        return

    # Abre o arquivo de vídeo usando OpenCV.
    video = cv2.VideoCapture('video.mp4') 


    while True:
        success, img = video.read()
        if not success:
            break

        # Processamento de imagem
        imgCinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #Aplicação de Threshold Adaptativo: Aplica um threshold adaptativo para binarizar a imagem, resultando em uma imagem em preto e branco.
        imgTh = cv2.adaptiveThreshold(imgCinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        imgMedian = cv2.medianBlur(imgTh, 5)
        # Cria um kernel (uma matriz 3x3 de 1s) e aplica a operação de dilatação à imagem para aumentar as áreas brancas, facilitando a contagem de "vagas".
        kernel = np.ones((3, 3), np.int8)
        imgDil = cv2.dilate(imgMedian, kernel)

        vacanciesOpen = 0 #Contador de Vagas: Inicializa um contador de vagas abertas

        # Processa as vagas usando as coordenadas
        for x, y, w, h in vacancies:
            vacancy = imgDil[y:y + h, x:x + w]
            count = cv2.countNonZero(vacancy)
            #Se o número de pixels não-zero for menor que 900, desenha um retângulo verde ao redor da vaga e incrementa o contador de vagas abertas. Caso contrário, desenha um retângulo vermelho.
            if count < 900:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                vacanciesOpen += 1
            else:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Adiciona informações no quadro, Retângulo de Informações: Desenha um retângulo verde no topo da imagem para exibir informações., Texto de Vagas: Adiciona texto na imagem indicando o número de vagas abertas.
        cv2.rectangle(img, (90, 0), (415, 60), (0, 255, 0), -1)
        cv2.putText(img, f'FREE: {vacanciesOpen}/69', (95, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 5)

        # Codifica o frame em formato JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        # Envia o frame como resposta para o navegador, Geração de Frames: Usa yield para enviar cada quadro como parte de uma resposta multipart, permitindo que o navegador receba e exiba o vídeo em tempo real.
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Rota para exibir o vídeo processado, Rota /video_feed: Define uma rota para fornecer o fluxo de vídeo. Chama a função generate_frames() e define o tipo MIME apropriado para transmissões de vídeo em tempo real.
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Rota principal para exibir a página HTML, Rota /: Define a rota principal que renderiza a página HTML (index.html). Se ocorrer um erro durante a renderização, imprime o erro e retorna uma mensagem de erro.
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Erro ao renderizar a página index: {e}")
        return "Erro ao carregar a página."

# Inicializa o servidor Flask, Execução do Servidor: Verifica se o arquivo está sendo executado diretamente e, se sim, inicia o servidor Flask em modo de depuração (debug), permitindo visualizar logs de erro e recarregar automaticamente as alterações.
if __name__ == "__main__":
    app.run(debug=True)
