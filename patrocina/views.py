import os
import io
import base64
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont, ImageOps
from django.core.files.base import ContentFile

def patrocinadores(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip().upper()
        cidade = request.POST.get('cidade', '').strip().upper()
        
        # Pega a foto (seja via upload normal ou via Base64 do Croppie)
        foto_base64 = request.POST.get('foto_cortada')
        foto_upload = request.FILES.get('foto')

        try:
            # 1. Carregar a Moldura e definir dimensões
            path_moldura = os.path.join(settings.BASE_DIR, 'static', 'img', 'moldura1.png')
            moldura = Image.open(path_moldura).convert("RGBA")
            largura_m, altura_m = moldura.size # 1080x1920 (proporcional)

            # 2. Processar a Foto do Usuário
            if foto_base64: # Se veio do Croppie
                format, imgstr = foto_base64.split(';base64,')
                foto_data = ContentFile(base64.b64decode(imgstr))
                foto_perfil = Image.open(foto_data).convert("RGBA")
            else: # Upload padrão
                foto_perfil = Image.open(foto_upload).convert("RGBA")

            # AJUSTE DA FOTO NO CÍRCULO:
            # O círculo na sua moldura está aproximadamente no centro superior.
            # Criamos um fundo transparente do tamanho da moldura e colamos a foto na posição do círculo.
            fundo_foto = Image.new("RGBA", moldura.size, (255, 255, 255, 0))
            
            # Redimensionar a foto para caber no círculo (ex: 750x750px)
            tamanho_circulo = 1030 
            foto_perfil = ImageOps.fit(foto_perfil, (tamanho_circulo, tamanho_circulo), Image.LANCZOS)
            
            # Coordenadas X e Y para centralizar a foto atrás do círculo da sua moldura
            pos_foto_x = (largura_m - tamanho_circulo) // 2
            pos_foto_y = 480 # Ajuste baseado na altura do círculo na moldura.jpg
            
            fundo_foto.paste(foto_perfil, (pos_foto_x, pos_foto_y))

            # 3. Sobreposição (Foto atrás, Moldura na frente)
            final = Image.alpha_composite(fundo_foto, moldura)
            draw = ImageDraw.Draw(final)

            # 4. Configuração das Fontes
            try:
                font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'ARIALBD.TTF') # Negrito
                font_nome = ImageFont.truetype(font_path, 70)
                font_cidade = ImageFont.truetype(font_path, 50)
            except:
                font_nome = font_cidade = ImageFont.load_default()

            # 5. Posicionamento do Texto nas Faixas Vermelhas
            # Centralizar Nome na primeira faixa vermelha
            w_n = draw.textlength(nome, font=font_nome)
            draw.text(((largura_m - w_n) / 2, 1720), nome, font=font_nome, fill="white")

            # Centralizar Cidade na segunda faixa vermelha
            w_c = draw.textlength(cidade, font=font_cidade)
            draw.text(((largura_m - w_c) / 2, 1815), cidade, font=font_cidade, fill="white")

            # 6. Salvar e Retornar
            byte_io = io.BytesIO()
            final.convert("RGB").save(byte_io, 'JPEG', quality=95)
            
            response = HttpResponse(byte_io.getvalue(), content_type="image/jpeg")
            response['Content-Disposition'] = f'attachment; filename="card_{nome}.jpg"'
            response.set_cookie("download_status", "concluido", max_age=30)
            return response

        except Exception as e:
            return HttpResponse(f"Erro: {e}")

    return render(request, 'patrocina.html')